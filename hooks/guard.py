"""Job Hunt Studio guards, run by Claude Code before each file edit and shell command (a PreToolUse hook).

Inside a Job Hunt Studio workspace (a folder that holds jhs.yaml), Claude may not:
1. edit, write, delete or move anything under resumes/approved/ or resumes/current/ (only the approve script,
   tools/approve_resume.py, writes there); a shell command that names a file there must be a known reader
   (cat, ls, grep, pdfinfo, the plugin's check scripts...) or copy from there to somewhere else;
2. delete, move or hand-make an approved-resume tag (jhs.yaml resume.tag_prefix, default resume-approved-v), or
   run git reset --hard;
3. push: git push, git subtree push, or gh repo create --push.
Everywhere else it allows everything, so the plugin never gets in the way of other projects. The guards cover
Claude's tool calls; what you type in your own terminal is up to you. They catch mistakes, not a determined
attacker: a script that writes files itself is not inspected.

Input: the hook's JSON on stdin (tool_name, tool_input, cwd). To block, it prints the reason on stderr and exits
with code 2, which Claude Code passes to Claude. Standard library only, Python 3.8 or later.

Try it by hand:  echo '{"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": "<workspace>"}' | python guard.py
"""
from __future__ import annotations

import base64
import glob
import json
import os
import re
import shlex
import sys
from pathlib import Path

PROTECTED = ("approved", "current")
DEFAULT_PREFIX = "resume-approved-v"
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

# Commands that only read the files they name (output redirection is checked separately).
READERS = {"cat", "type", "less", "more", "head", "tail", "ls", "dir", "tree", "wc", "file", "stat", "du", "diff",
           "cmp", "md5sum", "sha1sum", "sha256sum", "shasum", "grep", "egrep", "fgrep", "rg", "sort", "uniq", "cut",
           "jq", "echo", "printf", "basename", "dirname", "realpath", "readlink", "cygpath", "test", "[", "nl",
           "tac", "od", "xxd", "strings", "pdfinfo", "pdffonts", "open", "xdg-open", "explorer", "code",
           "get-content", "gc", "get-childitem", "gci", "get-item", "gi", "get-itemproperty", "gp", "test-path",
           "resolve-path", "split-path", "join-path", "convert-path", "select-string", "sls", "get-filehash",
           "format-hex", "get-acl", "write-output", "write-host", "invoke-item", "ii", "latexdiff", "bat", "sed",
           "perl", "awk", "gawk", "find", "sort", "uniq", "xxd", "tree"}
# Readers that write when given an output flag or a second file name.
READER_OUTPUT_FLAGS = {"sort": ("-o", "--output"), "tree": ("-o",)}
READER_SECOND_IS_OUTPUT = {"uniq", "xxd"}
# Programs that run a command given as a string (script -c "...", ssh host "...", watch "...").
STRING_RUNNERS = {"script", "su", "ssh", "watch", "flock", "parallel", "wsl", "runas", "busybox"}
PERL_WRITES = re.compile(r"unlink|rename|system|truncate|open\s*\(?[^;]*>|`")
# Plugin scripts that only read the files they are given, and scripts whose first operand is an output folder.
READ_ONLY_TOOLS = {"ats_check.py", "fact_check.py", "resume_lint.py", "preflight.py", "practice.py", "ledger.py"}
# The approve script is the one program that writes approved versions; its arguments are a summary and a score.
TRUSTED_TOOLS = {"approve_resume.py"}
DEST_FIRST_TOOLS = {"visual_check.py"}
DELETE_VERBS = {"rm", "rmdir", "unlink", "shred", "del", "erase", "rd", "remove-item", "ri", "clear-content",
                "mv", "move", "move-item", "mi", "rename-item", "ren", "rni"}
# Commands that read their sources and write only to a destination (the last operand, or -t, -o, -Destination).
COPY_VERBS = {"cp", "copy", "copy-item", "cpi", "install", "rsync", "ln", "xcopy", "robocopy", "pdftoppm",
              "pdftotext", "pdfimages", "pdftocairo", "pandoc", "magick", "convert"}
PS_WRITERS = {"set-content", "add-content", "out-file", "clear-content", "new-item", "sc", "ac", "tee-object"}
CMD_SWITCH_VERBS = {"xcopy", "robocopy", "copy", "move", "del", "erase", "rd", "rmdir", "ren", "type", "dir"}
WRAPPERS = {"sudo", "command", "builtin", "exec", "time", "nohup", "env", "xargs", "nice", "ionice", "timeout",
            "winpty", "stdbuf", "setsid", "if", "then", "else", "elif", "do", "while", "until", "!", "{", "}",
            "try", "catch", "finally", "foreach", "%", "foreach-object", "where-object", "?"}
WRAPPER_OPTS_WITH_VALUE = {"-n", "-s", "-k", "-u", "-g", "-C", "-S", "-I", "-P", "-L", "-d", "-E", "-a", "--signal",
                           "--kill-after", "--adjustment", "--user", "--group", "--chdir"}
SHELLS = {"bash", "sh", "zsh", "dash"}
POWERSHELLS = {"pwsh", "powershell"}
POWERSHELL_OPTS_WITH_VALUE = ("executionpolicy", "windowstyle", "outputformat", "inputformat", "workingdirectory",
                              "configurationname", "version", "settingsfile", "custompipename")
EVALS = {"eval", "iex", "invoke-expression"}
PYTHONS = {"python", "python3", "py"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env",
                       "--exec-path"}
TAG_LIST_FLAGS = {"-l", "--list", "-n", "-v", "--verify", "--contains", "--no-contains", "--points-at", "--merged",
                  "--no-merged"}
SEPARATOR_CHARS = set(";&|()<>")
FIND_ACTIONS = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}
PY_WRITES = re.compile(r"write|unlink|remove|rmtree|rename|shutil|truncate|os\.system|subprocess|"
                       r"open\([^)]*['\"][wax+]")
DOTNET_WRITE = re.compile(r"\]::(Delete|Move|Copy|Replace|Write\w*|Append\w*|Create\w*|Set\w*)\b", re.I)

# Ways to spell "the folder I am in", the project folder and the home folder: replaced by marks before the command
# is split into words, and by the real folders when a path is resolved.
CWD_MARK, PROJECT_MARK, ROOT_MARK, HOME_MARK = "JHSCWDMARK", "JHSPROJECTMARK", "JHSROOTMARK", "JHSHOMEMARK"
SUBSTITUTIONS = [
    (re.compile(r"\$\(\s*git\s+rev-parse\s+--show-toplevel\s*\)|`\s*git\s+rev-parse\s+--show-toplevel\s*`"), ROOT_MARK),
    (re.compile(r"\$\(\s*pwd\s*\)|`\s*pwd\s*`|\$\{PWD\}|\$PWD(\.Path)?\b|\$env:PWD\b|%CD%|"
                r"\$?\(\s*Get-Location\s*\)(\.Path)?", re.I), CWD_MARK),
    (re.compile(r"\$\{CLAUDE_PROJECT_DIR\}|\$CLAUDE_PROJECT_DIR\b|\$env:CLAUDE_PROJECT_DIR\b|"
                r"%CLAUDE_PROJECT_DIR%", re.I), PROJECT_MARK),
    (re.compile(r"\$\{HOME\}|\$HOME\b|\$env:USERPROFILE\b|\$env:HOME\b|%USERPROFILE%", re.I), HOME_MARK),
]
STATE = {"project": "", "origin": None}  # the session's project folder and the workspace it started in


class Blocked(Exception):
    pass


# ---------------------------------------------------------------- paths

def find_workspace(start: Path) -> Path | None:
    """The nearest folder at or above `start` that holds jhs.yaml."""
    try:
        here = start.resolve()
        for folder in [here, *here.parents]:
            if (folder / "jhs.yaml").is_file():
                return folder
    except (OSError, ValueError):
        pass
    return None


def tag_prefix(root: Path) -> str:
    """resume.tag_prefix from jhs.yaml, read without PyYAML (the hook may run outside the workspace venv)."""
    try:
        text = (root / "jhs.yaml").read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_PREFIX
    m = re.search(r"^\s+tag_prefix:\s*[\"']?([^\"'\s#]+)", text, re.M)
    return m.group(1) if m else DEFAULT_PREFIX


def resolve(arg: str, cwd: Path) -> Path:
    text = arg.replace("\\", "/")
    for mark, value in ((CWD_MARK, str(cwd)), (PROJECT_MARK, STATE["project"] or str(cwd)),
                        (ROOT_MARK, str(find_workspace(cwd) or cwd)), (HOME_MARK, os.path.expanduser("~"))):
        if mark in text:
            text = text.replace(mark, value.replace("\\", "/"))
    if os.name == "nt":
        text = re.sub(r"^//[?.]/", "", text)                                   # \\?\C:\...
        text = re.sub(r"^/cygdrive/([A-Za-z])(?=/|$)", r"\1:", text)            # /cygdrive/c/...
        text = re.sub(r"^/([A-Za-z])(?=/|$)", r"\1:", text)                     # Git Bash /c/...
        if re.fullmatch(r"[A-Za-z]:", text):
            text += "/"
    path = Path(os.path.expanduser(text))
    return Path(os.path.normpath(str(path if path.is_absolute() else cwd / path)))


def braces(text: str) -> list[str]:
    """Bash brace expansion: resumes/{approved,current} names two folders."""
    m = re.search(r"\{([^{}]*,[^{}]*)\}", text)
    if not m:
        return [text]
    return [x for part in m.group(1).split(",") for x in braces(text[:m.start()] + part + text[m.end():])]


def expand(arg: str, cwd: Path) -> list[Path]:
    """The paths an argument names, with braces and wildcards expanded (rm resumes/*)."""
    out: list[Path] = []
    for text in braces(arg)[:64]:
        path = resolve(text, cwd)
        found = [Path(m) for m in glob.glob(str(path))] if any(ch in text for ch in "*?[") else []
        out.extend(found or [path])
    return out


def key(path: Path) -> str:
    """A path in comparable form: links, junctions and Windows short names (JHS-E2~1) resolved, case folded."""
    try:
        text = os.path.realpath(str(path))
    except (OSError, ValueError):
        text = os.path.normpath(str(path))
    return os.path.normcase(text).rstrip("/" + os.sep)


def protected_dirs(root: Path) -> list[Path]:
    return [root / "resumes" / name for name in PROTECTED]


def inside(path: Path) -> Path | None:
    """The protected folder that holds `path` (or is `path`), or None."""
    root = find_workspace(path.parent)
    if root is None:
        return None
    p = key(path)
    for d in protected_dirs(root):
        k = key(d)
        if p == k or p.startswith(k + os.sep):
            return d
    return None


def covers(path: Path, cwd: Path) -> Path | None:
    """Like inside(), and also true when `path` holds a protected folder or the workspace itself (rm -rf ..)."""
    hit = inside(path)
    if hit:
        return hit
    p = key(path)
    for root in {r for r in (find_workspace(path), find_workspace(cwd), STATE["origin"]) if r}:
        for d in protected_dirs(root):
            if d.exists() and key(d).startswith(p + os.sep):
                return d
    return None


def is_dynamic(arg: str) -> bool:
    """An argument whose value the guard cannot know: a variable or a command substitution."""
    return "$" in arg or "`" in arg


def mentioned(words: list[str], cwd: Path, broad: bool) -> Path | None:
    """A protected folder that some word of the command names (`broad`: or a folder that holds one). A word may
    be NAME=path, or a longer string (code, a quoted command) with a path inside it."""
    for w in words:
        candidates = [w] + ([w.split("=", 1)[1]] if "=" in w else []) + embedded(w)
        for candidate in candidates:
            for path in expand(candidate, cwd):
                hit = covers(path, cwd) if broad else inside(path)
                if hit:
                    return hit
                root = find_workspace(path)
                if root and key(path) == key(root / "resumes"):
                    return root / "resumes"
    return None


def embedded(text: str) -> list[str]:
    """Paths into a protected folder written inside a longer string: python -c "os.remove('resumes/current/x')"."""
    return re.findall(r"[A-Za-z0-9_./\\:~-]*resumes[/\\]+(?:approved|current)[A-Za-z0-9_./\\-]*", text)


def why_path(path: Path, what: str) -> str:
    return (f"Job Hunt Studio guard: {what} {path} is blocked. resumes/approved/ and resumes/current/ hold the "
            "approved resume versions; only the approve script (tools/approve_resume.py) writes there, after the "
            "user's explicit OK. Change the base resume or a tailored copy instead.")


def why_unknown(path: Path, verb: str) -> str:
    return (f"Job Hunt Studio guard: {verb} is blocked here because the command names {path} and the guard cannot "
            "tell which files it will change (a variable, a pipeline or a command substitution decides). "
            "resumes/approved/ and resumes/current/ hold the approved resume versions; name the files plainly, "
            "outside those folders.")


# ---------------------------------------------------------------- edits

def check_edit(tool_input: dict, cwd: Path) -> None:
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
    if raw:
        path = resolve(str(raw), cwd)
        if inside(path):
            raise Blocked(why_path(path, "changing"))


# ---------------------------------------------------------------- commands

def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: a commit message is text, not commands."""
    out, ends, keep = [], [], False
    for line in command.split("\n"):
        if ends:
            if line.strip() == ends[0]:
                ends.pop(0)
                keep = keep and bool(ends)
            elif keep:
                out.append(line)  # a heredoc fed to a shell is commands, not text
            continue
        out.append(line)
        found = [m.group(2) for m in re.finditer(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)]
        if found:
            keep = bool(re.search(r"(?:^|[;&|(]\s*)(?:bash|sh|zsh|dash)\b[^;&|]*<<", line))
            ends.extend(found)
    return "\n".join(out)


def tokens(command: str, ps: bool) -> list[str]:
    """The words and separators of a command. `ps`: PowerShell or cmd syntax, where \\ is a path separator."""
    text = strip_heredocs(command)
    for pattern, mark in SUBSTITUTIONS:
        text = pattern.sub(mark, text)
    if ps:
        text = text.replace("\\", "/").replace(",", " ").replace("{", " { ").replace("}", " } ")
    else:
        text = re.sub(r"(?<=[A-Za-z0-9_.:~?-])\\(?=[A-Za-z0-9_.~?-])", "/", text)  # Windows paths, not escapes
        text = re.sub(r"(?<!\S)\\\\(?=[?.])", "//", text)                           # \\?\C:\... long paths
    text = text.replace("`", " ; ").replace("\n", " ; ")
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:  # unbalanced quotes: a plain split is good enough to look for the patterns
        return re.findall(r"[;&|()<>]+|[^\s;&|()<>]+", text)


def segments(toks: list[str]):
    """The simple commands in a token list, each as (words, redirection targets, fed by a pipe, here-strings)."""
    words: list[str] = []
    targets: list[str] = []
    fed: list[str] = []
    piped = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t and set(t) <= SEPARATOR_CHARS:
            if ("<" in t or ">" in t) and words and words[-1].isdigit():
                words.pop()  # the file descriptor in 2> or 2>&1
            if ">" in t:
                if i + 1 < len(toks) and not (t.endswith("&") and toks[i + 1].isdigit()):
                    targets.append(toks[i + 1])
                i += 2
                continue
            if "<" in t:
                if t == "<<<" and i + 1 < len(toks):
                    fed.append(toks[i + 1])  # bash <<< 'git push'
                i += 2
                continue
            if words or targets:
                yield words, targets, piped, fed
            words, targets, fed = [], [], []
            piped = "|" in t and "||" not in t
        else:
            words.append(t)
        i += 1
    if words or targets:
        yield words, targets, piped, fed


def unwrap(words: list[str]) -> tuple[list[str], bool]:
    """Drop wrappers (sudo, env, timeout 60, xargs and their options) and leading VAR=value assignments.
    Returns the remaining words and whether xargs was one of the wrappers (its arguments come from stdin)."""
    via_xargs = False
    while words:
        w = words[0]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", w):
            words = words[1:]
        elif w.lower() in WRAPPERS:
            via_xargs = via_xargs or w.lower() == "xargs"
            words = words[1:]
            while words:
                if words[0] in WRAPPER_OPTS_WITH_VALUE:
                    words = words[2:]
                elif words[0].startswith("-") and words[0] != "--":
                    words = words[1:]
                elif re.fullmatch(r"\d+(\.\d+)?[smhd]?", words[0]):  # timeout 60, nice 5
                    words = words[1:]
                else:
                    break
        else:
            break
    return words, via_xargs


def program(word: str) -> str:
    name = os.path.basename(word.replace("\\", "/")).lower()
    return name[:-4] if name.endswith(".exe") else name


def operands(args: list[str]) -> list[str]:
    out, after_dashes = [], False
    for a in args:
        if a == "--" and not after_dashes:
            after_dashes = True
        elif after_dashes or not (a.startswith("-") and len(a) > 1):
            out.append(a)
    return out


def path_args(args: list[str]) -> list[str]:
    """Every argument that may name a file: operands, values after = (-outdir=x, of=x) and after -o/-Path style flags."""
    out = list(operands(args))
    for i, a in enumerate(args):
        if "=" in a:
            out.append(a.split("=", 1)[1])
        if a.startswith("-") and "=" not in a and i + 1 < len(args) and not args[i + 1].startswith("-"):
            out.append(args[i + 1])
    return out


def git_parts(args: list[str], cwd: Path) -> tuple[str, list[str], Path]:
    """(subcommand, its arguments, the folder git runs in) for `git <global options> <subcommand> ...`.
    Follows -C, --git-dir and --work-tree to the repository they name, and -c alias.x=push to the real command."""
    aliases: dict[str, list[str]] = {}
    i = 0
    while i < len(args):
        a = args[i]
        name, _, value = a.partition("=")
        if name in GIT_OPTS_WITH_VALUE and (value or i + 1 < len(args)):
            if not value:
                i += 1
                value = args[i]
            if name == "-C":
                cwd = resolve(value, cwd)
            elif name in ("--git-dir", "--work-tree"):
                target = resolve(value, cwd)
                cwd = target.parent if target.name == ".git" else target
            elif name == "-c" and value.lower().startswith("alias.") and "=" in value:
                alias, _, command = value[6:].partition("=")
                aliases[alias.lower()] = command.split()
            i += 1
        elif a.startswith("-"):
            i += 1
        else:
            sub, rest = a.lower(), args[i + 1:]
            if sub in aliases and aliases[sub]:
                sub, rest = aliases[sub][0].lower(), aliases[sub][1:] + rest
            return sub, rest, cwd
    return "", [], cwd


PUSH_REASON = ("Job Hunt Studio guard: pushing is blocked in a job-search workspace. It holds personal data and stays "
               "on this computer; if you back it up to a private repository, push from your own terminal.")


def check_git(args: list[str], cwd: Path, command: str, via_xargs: bool, all_words: list[str]) -> None:
    sub, rest, gcwd = git_parts(args, cwd)
    names = operands(rest)
    if sub in ("rm", "mv", "clean", "checkout", "restore"):
        index_only = sub == "restore" and {"--staged", "-S"} & set(rest) and not {"--worktree", "-W"} & set(rest)
        if not index_only:
            for a in names:
                for path in expand(a, gcwd):
                    if covers(path, gcwd):
                        raise Blocked(why_path(path, f"git {sub} on"))
            if any(is_dynamic(a) for a in names):
                hit = mentioned(all_words, gcwd, broad=False)
                if hit:
                    raise Blocked(why_unknown(hit, f"git {sub}"))
    root = find_workspace(gcwd)
    if root is None:
        return
    if sub in ("push", "send-pack") or (sub == "subtree" and "push" in rest):
        raise Blocked(PUSH_REASON)
    if sub == "reset" and {"--hard", "--merge", "--keep"} & set(rest):
        raise Blocked("Job Hunt Studio guard: git reset --hard is blocked in a job-search workspace: it can undo an "
                      "approved version's files and discard uncommitted work. Run it yourself if you mean it.")
    prefix = tag_prefix(root)
    if sub == "tag":
        flags = {a.split("=")[0] for a in rest if a.startswith("-")}
        listing = flags & TAG_LIST_FLAGS or any(re.fullmatch(r"-n\d+", f) for f in flags)
        unknown = via_xargs or not names or any(set(n) & set("$*?`{}") for n in names)
        if flags & {"-d", "--delete", "-f", "--force"} and (prefix in command or unknown):
            raise Blocked(f"Job Hunt Studio guard: deleting or moving an approved resume tag ({prefix}<N>) is "
                          "blocked (or the tags named cannot be told apart from them). Approved versions never "
                          "change; a new version gets the next number through the approve script.")
        if not listing and any(n.startswith(prefix) for n in names):
            raise Blocked(f"Job Hunt Studio guard: approved resume tags ({prefix}<N>) are made only by the approve "
                          "script (tools/approve_resume.py), after review-resume returns READY and the user says "
                          "OK.")
    if any(f"refs/tags/{prefix}" in a for a in rest) and sub in ("update-ref", "symbolic-ref", "fetch", "pull",
                                                                    "replace"):
        raise Blocked(f"Job Hunt Studio guard: changing an approved resume tag ({prefix}<N>) is blocked.")
    if sub == "update-ref" and "--stdin" in rest:
        raise Blocked("Job Hunt Studio guard: git update-ref --stdin is blocked in a job-search workspace: the "
                      f"guard cannot see which refs it changes, and approved resume tags ({prefix}<N>) never change.")


def check_git_files(args: list[str], cwd: Path, deleting: bool) -> None:
    """Changing tags behind git's back: .git/refs/tags/<prefix>N, packed-refs, or deleting .git itself."""
    root = find_workspace(cwd) or STATE["origin"]
    if root is None:
        return
    prefix = tag_prefix(root)
    git_dir = root / ".git"
    whole = {key(git_dir), key(git_dir / "refs"), key(git_dir / "refs" / "tags")}
    for a in args:
        flat = a.replace("\\", "/")
        if f"refs/tags/{prefix}" in flat or flat.rstrip("/").endswith("packed-refs"):
            raise Blocked(f"Job Hunt Studio guard: changing approved resume tags ({prefix}<N>) by hand is blocked.")
        if any(key(p) in whole for p in expand(a, cwd)) and (deleting or key(resolve(a, cwd)) != key(git_dir)):
            raise Blocked("Job Hunt Studio guard: changing or deleting the workspace's .git folder (it holds the "
                          "approved resume tags) is blocked.")


def flag_is(arg: str, name: str) -> bool:
    """PowerShell accepts any unambiguous prefix of a parameter name: -c, -com, -Command; -e, -enc, -EncodedCommand."""
    flag = arg.lower().lstrip("-/")
    if name == "encodedcommand" and flag == "ec":  # PowerShell's own short alias
        return arg[:1] in "-/"
    return arg[:1] in "-/" and bool(flag) and name.startswith(flag)


def inner_command(verb: str, args: list[str]) -> tuple[str, bool] | None:
    """(the command string a shell, PowerShell, cmd, eval or Start-Process wrapper runs, whether it is in
    PowerShell or cmd syntax), or None."""
    low = [a.lower() for a in args]
    if verb in SHELLS:
        for i, a in enumerate(low):
            if re.fullmatch(r"-[a-z]*c", a) and i + 1 < len(args):
                return args[i + 1], False
        return None
    if verb in POWERSHELLS:
        i, rest = 0, []
        while i < len(args):
            a = args[i]
            if flag_is(a, "encodedcommand") and i + 1 < len(args):
                try:
                    return base64.b64decode(args[i + 1] + "===").decode("utf-16-le", "replace"), True
                except ValueError:
                    return args[i + 1], True
            if flag_is(a, "command") and i + 1 < len(args):
                return " ".join(args[i + 1:]), True
            if flag_is(a, "file"):
                return None
            if a[:1] == "-" and any(name.startswith(a.lower().lstrip("-")) for name in POWERSHELL_OPTS_WITH_VALUE):
                i += 2
                continue
            if a[:1] != "-":
                rest.append(a)
            i += 1
        return (" ".join(rest), True) if rest else None  # powershell "git push": the string is the command
    if verb == "cmd":
        for i, a in enumerate(low):
            if a in ("/c", "/k", "//c", "//k", "-c") and i + 1 < len(args):
                return " ".join(args[i + 1:]), True
        return None
    if verb == "eval":
        return " ".join(args), False
    if verb in EVALS:
        return " ".join(args), True
    if verb == "start":  # cmd's start launches a program or opens a file
        return " ".join(a for a in args if a and not a.startswith("/")), True
    if verb in ("start-process", "saps", "start-job", "invoke-command", "icm"):
        file, rest = "", []
        for i, a in enumerate(low):
            if a in ("-filepath", "-file") and i + 1 < len(args):
                file = args[i + 1]
            if a in ("-argumentlist", "-args") and i + 1 < len(args):
                rest = args[i + 1:]
        names = [a for a in operands(args) if a not in ("{", "}")]
        if verb in ("start-job", "invoke-command", "icm"):
            return " ".join(names), True  # the script block's words
        file = file or (names[0] if names else "")
        if not rest and len(names) > 1:
            rest = names[1:]
        return (f"{file} {' '.join(rest)}".strip(), True) if file else None
    return None


def classify(verb: str, args: list[str], names: list[str]) -> tuple[str, list[str]]:
    """How a command treats the files it names: ("reader", []), ("delete", []), ("copy", destinations), ("other", [])."""
    low = [a.lower() for a in args]
    if verb in DELETE_VERBS:
        return "delete", []
    if verb in ("mkdir", "md") or (verb in ("new-item", "ni") and "directory" in low):
        return "mkdir", []
    if verb in ("rsync", "robocopy") and {"--remove-source-files", "/mov", "/move", "/mir", "/purge"} & set(low):
        return "delete", []  # these remove the source or prune the destination
    if verb == "robocopy":
        return "copy", names[1:2]  # robocopy <source> <destination> [files]
    if verb in COPY_VERBS:
        dests = [args[i + 1] for i, a in enumerate(low[:-1])
                 if a in ("-t", "--target-directory", "-o", "--output", "-destination", "-dest")]
        dests += [a.split("=", 1)[1] for a in args if re.match(r"--(target-directory|output)=", a)]
        dests += [a[2:] for a in args if re.match(r"^-t[^-]", a) and verb in ("cp", "install", "ln")]  # cp -tDIR
        return "copy", dests or names[-1:]
    if verb == "pdftk":
        return "copy", [args[i + 1] for i, a in enumerate(low[:-1]) if a == "output"]
    if verb == "qpdf":
        return "copy", (names[1:2] if len(names) > 1 else [])
    if verb == "exiftool":
        return ("other" if any("=" in a for a in args) or "-overwrite_original" in low else "reader"), []
    if verb == "mutool":
        return ("reader" if low[:1] and low[0] in ("info", "show", "pages") else "other"), []
    if verb in ("tar", "bsdtar"):
        extract = any(re.fullmatch(r"-[A-Za-z]*x[A-Za-z]*", a) or a in ("--extract", "--get") for a in args) \
            or bool(args and re.fullmatch(r"[A-Za-z]*x[A-Za-z]*", args[0]))
        if extract:
            dirs = [args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-C", "--directory")]
            dirs += [a.split("=", 1)[1] for a in args if a.startswith("--directory=")]
            return "copy", dirs or ["."]
        archive = [args[i + 1] for i, a in enumerate(args[:-1]) if re.fullmatch(r"-?[A-Za-z]*f", a)]
        return "copy", archive[:1]
    if verb == "zip":
        return "copy", names[:1]
    if verb == "unzip":
        return "copy", [args[i + 1] for i, a in enumerate(args[:-1]) if a == "-d"] or ["."]
    if verb in PYTHONS or verb.startswith("python3."):
        if "-c" in args:
            code = (args + [""])[args.index("-c") + 1]
            return ("other" if PY_WRITES.search(code) else "reader"), []
        script = next((a for a in args if a.lower().endswith(".py")), "")
        base = os.path.basename(script.replace("\\", "/"))
        if base in READ_ONLY_TOOLS or base in TRUSTED_TOOLS:
            return "reader", []
        if base in DEST_FIRST_TOOLS:
            after = names[names.index(script) + 1:] if script in names else names
            return "copy", after[:1]
        return "other", []
    if verb in READERS:
        if verb in READER_OUTPUT_FLAGS:
            flags = READER_OUTPUT_FLAGS[verb]
            outs = [args[i + 1] for i, a in enumerate(args[:-1]) if a in flags]
            outs += [a.split("=", 1)[1] for a in args if a.split("=", 1)[0] in flags and "=" in a]
            outs += [a[2:] for a in args if a[:2] in flags and len(a) > 2 and not a.startswith("--")]
            if outs:
                return "copy", outs
        if verb in READER_SECOND_IS_OUTPUT and len(names) > 1:
            return "copy", names[1:2]
        if verb == "sed" and any(re.match(r"^-[A-Za-z0-9]*i", a) or a.startswith("--in-place") for a in args):
            return "other", []
        if verb == "perl" and (any(re.match(r"^-(?![MI])[A-Za-z0-9]*i", a) for a in args)
                               or any(PERL_WRITES.search(a) for a in args)):
            return "other", []
        if verb in ("awk", "gawk") and ("inplace" in args or "--include=inplace" in args):
            return "other", []
        if verb == "find" and FIND_ACTIONS & set(low):
            return "delete", []
        return "reader", []
    return "other", []


def check_words(words: list[str], targets: list[str], piped: bool, cwd: Path, command: str, all_words: list[str],
                depth: int, ps: bool, fed: tuple[str, ...] = ()) -> Path:
    """Check one simple command; returns the folder the next command runs in (cd changes it)."""
    for t in targets:
        check_git_files([t], cwd, deleting=False)
        for path in expand(t, cwd):
            if inside(path):
                raise Blocked(why_path(path, "writing to"))
        if is_dynamic(t):
            hit = mentioned(all_words, cwd, broad=False)
            if hit:
                raise Blocked(why_unknown(hit, "writing to a file"))
    words, via_xargs = unwrap(words)
    if not words:
        return cwd
    verb, args = program(words[0]), words[1:]
    if verb in CMD_SWITCH_VERBS:
        args = [a for a in args if not re.fullmatch(r"/[A-Za-z?]{1,4}(:\S*)?", a)]  # cmd switches: /Y /E /MIR
    names = operands(args)
    if verb in ("cd", "pushd", "set-location", "sl", "chdir"):
        return resolve(names[0], cwd) if names else cwd
    inner = inner_command(verb, args)
    if inner is not None:
        check_command(inner[0], cwd, depth + 1, inner[1] or ps)
        return cwd
    if verb in SHELLS:  # commands that reach a shell on its standard input: bash <<< '...', echo '...' | bash
        for text in list(fed) + ([w for w in all_words if " " in w.strip()] if piped else []):
            check_command(text, cwd, depth + 1, False)
    if verb in STRING_RUNNERS:
        for text in (a for a in args if " " in a.strip()):  # script -qc 'git push', ssh host 'git push'
            check_command(text, cwd, depth + 1, ps)
    if verb == "git":
        check_git(args, cwd, command, via_xargs, all_words)
        return cwd
    if verb == "gh":
        if args[:2] == ["repo", "create"] and any(a == "--push" or a.startswith("--push=") for a in args) \
                and find_workspace(cwd):
            raise Blocked(PUSH_REASON)
        return cwd

    mode, dests = classify(verb, args, names)
    if mode == "reader":
        return cwd
    check_git_files(path_args(args), cwd, deleting=(mode == "delete"))
    home = inside(cwd)
    if home and not (mode == "copy" and dests and not any(inside(p) for d in dests for p in expand(d, cwd))):
        raise Blocked(why_path(home, f"running {verb} inside"))
    in_workspace = find_workspace(cwd) or STATE["origin"]
    unknown = [a for a in (dests if mode == "copy" else path_args(args)) if is_dynamic(a)]
    no_names = mode == "delete" and not names  # Remove-Item (Resolve-Path ...), ... | Remove-Item
    from_pipe = piped and (mode == "delete" or (verb in PS_WRITERS and not names))
    if in_workspace and (via_xargs or unknown or from_pipe or no_names):
        hit = mentioned(all_words, cwd, broad=mode == "delete" and (via_xargs or from_pipe))
        if hit:
            raise Blocked(why_unknown(hit, verb))
    if mode == "mkdir":  # making the (empty) folder itself is harmless; anything inside it is not
        for a in names:
            for path in expand(a, cwd):
                home = inside(path)
                if home and key(path) != key(home):
                    raise Blocked(why_path(path, "creating"))
    elif mode == "delete":
        for a in names:
            for path in expand(a, cwd):
                if covers(path, cwd):
                    raise Blocked(why_path(path, "deleting or moving"))
    elif mode == "copy":
        for a in dests:
            for path in expand(a, cwd):
                if inside(path):
                    raise Blocked(why_path(path, "copying into"))
    else:
        for a in path_args(args):
            for candidate in [a] + embedded(a):  # also a path written inside code: python -c "os.remove('...')"
                for path in expand(candidate, cwd):
                    if inside(path):
                        raise Blocked(why_path(path, f"running {verb} on"))
        for i, w in enumerate(args):  # a wrapper the guard does not know (flock, watch ...) in front of git or gh
            if program(w) in ("git", "gh"):
                return check_words(args[i:], [], piped, cwd, command, all_words, depth, ps)
    return cwd


def check_command(command: str, cwd: Path, depth: int = 0, ps: bool = False) -> None:
    if depth > 4:
        return
    toks = tokens(command, ps)
    all_words = [t for t in toks if not (t and set(t) <= SEPARATOR_CHARS)]
    if DOTNET_WRITE.search(command):
        hit = mentioned(all_words, cwd, broad=False)
        if hit:
            raise Blocked(why_unknown(hit, "a .NET file call"))
    for words, targets, piped, fed in segments(toks):
        cwd = check_words(words, targets, piped, cwd, command, all_words, depth, ps, tuple(fed))


# ---------------------------------------------------------------- main

def decide(event: dict) -> str | None:
    """The reason to block this tool call, or None to let it through."""
    tool = event.get("tool_name") or ""
    tool_input = event.get("tool_input") or {}
    cwd = resolve(str(event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()), Path.cwd())
    STATE["project"] = os.environ.get("CLAUDE_PROJECT_DIR") or str(cwd)
    STATE["origin"] = find_workspace(cwd) or find_workspace(resolve(STATE["project"], cwd))
    try:
        if tool in EDIT_TOOLS:
            check_edit(tool_input, cwd)
        elif tool in SHELL_TOOLS:
            check_command(str(tool_input.get("command") or ""), cwd, ps=(tool == "PowerShell"))
    except Blocked as exc:
        return str(exc)
    return None


def main() -> int:
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
    except ValueError:
        return 0
    try:
        reason = decide(event)
    except Exception as exc:  # a bug here must not stop every tool call: say so and let the call through
        print(f"Job Hunt Studio guard could not check this call ({type(exc).__name__}: {exc}).", file=sys.stderr)
        return 1
    if reason:
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
