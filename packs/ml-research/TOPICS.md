# ml-research pack: interview topics

The areas an interview for a machine learning engineer, applied scientist or research engineer draws from. `mock-interview` uses them: each area name (the bold word) is the file name of your revision notes under `interview/notes/` and the area column of `interview/PRACTICE_LOG.md`. Readings are primary sources and standard texts; prefer them over blog summaries.

Core areas come up in most interviews for these roles. Field areas depend on your work and the postings you apply to: `mock-interview plan` suggests the ones that match your Ledger.

## Probe styles

Use a mix inside every round:
- **Explain**: "What is X and why does it work?" Intuition first, then mechanism.
- **Derive**: write the math (a gradient, a loss, a complexity or memory estimate).
- **Compare**: X versus Y, and when to choose each.
- **Debug**: "Training loss goes to NaN at step 2,000", "offline NDCG went up but clicks went down". What do you check, in what order?
- **Estimate**: memory for training or inference, throughput, cost, sample size.
- **Design**: an open problem under constraints (latency, data, budget).
- **Implement**: write it in NumPy, PyTorch or plain Python (coding area).
- **Connect**: "Where did this come up in your own work?"

## Core areas

1. **ml-fundamentals**: bias and variance, overfitting and regularization (L1, L2, dropout, early stopping), cross-validation and data leakage, loss functions, gradient descent and optimizers (SGD, momentum, Adam, AdamW), learning-rate schedules and warmup, class imbalance, metrics (precision, recall, F1, ROC-AUC versus PR-AUC, calibration), linear and logistic regression, trees, bagging and boosting, k-means and PCA.
   Reading: Stanford CS229 notes; Géron, *Hands-On Machine Learning*; Hastie, Tibshirani and Friedman, *The Elements of Statistical Learning*.
2. **math-stats**: probability and Bayes, MLE and MAP, common distributions, expectation and variance, entropy, cross-entropy and KL divergence, linear algebra (matrix products, eigendecomposition, SVD, rank), hypothesis tests, confidence intervals, the bootstrap, power and sample size.
   Reading: Deisenroth, Faisal and Ong, *Mathematics for Machine Learning*; Wasserman, *All of Statistics*.
3. **deep-learning**: backpropagation, initialization, vanishing and exploding gradients, residual connections, normalization (BatchNorm, LayerNorm, RMSNorm), dropout, CNN and RNN basics, embeddings, mixed precision (fp16, bf16, loss scaling), gradient clipping, debugging a training run.
   Reading: Goodfellow, Bengio and Courville, *Deep Learning*; Karpathy, "A Recipe for Training Neural Networks" (2019).
4. **evaluation**: offline metrics and their limits, test-set hygiene and leakage, data contamination, error analysis and slicing, human evaluation and agreement (Cohen's kappa), LLM-as-a-judge and its biases (position, verbosity, self-preference), significance (paired bootstrap, confidence intervals), online A/B tests and guardrail metrics, choosing metrics that match the product.
   Reading: Kohavi, Tang and Xu, *Trustworthy Online Controlled Experiments*; Zheng et al. 2023 ("Judging LLM-as-a-Judge"); Liang et al. 2022 (HELM).
5. **ml-system-design**: the frame (clarify the goal and constraints, data and labels, a baseline, the model, offline evaluation, serving, monitoring and feedback loops, iteration); training and serving skew, drift, cold start, cost. Classic prompts: a recommender or ranking system, search, an LLM assistant over company documents, an evaluation pipeline for an LLM product, fraud or anomaly detection, content moderation.
   Reading: Huyen, *Designing Machine Learning Systems*; Aminian and Xu, *Machine Learning System Design Interview*.
6. **mlops-distributed**: experiment tracking, data and model versioning, tests for ML code and models, deployment patterns (batch, online, shadow, canary), monitoring, data parallel (DDP) versus sharded (FSDP, ZeRO) versus tensor and pipeline parallel, GPU memory for training (weights, gradients, optimizer states, activations).
   Reading: Sculley et al. 2015 ("Hidden Technical Debt in Machine Learning Systems"); Rajbhandari et al. 2020 (ZeRO); Zhao et al. 2023 (PyTorch FSDP).
7. **ml-coding**: implement from scratch in NumPy or PyTorch: numerically stable softmax and cross-entropy, logistic regression by gradient descent, k-means, a training loop with an optimizer step, scaled dot-product attention with a causal mask, top-k and top-p sampling, ROC-AUC, NDCG; plus everyday Python (dictionaries, sorting, two pointers, heaps) at an easy to medium level.
   Practice: write it, run it on a tiny input, state the complexity.

## Field areas

8. **transformers-llms**: scaled dot-product and multi-head attention and its cost in sequence length, positional encodings (sinusoidal, learned, RoPE), decoder-only models and causal masking, tokenization (BPE), the KV cache, MQA and GQA, pretraining objectives, scaling laws, mixture of experts, long context, FlashAttention, decoding (greedy, beam, temperature, top-k, top-p).
   Reading: Vaswani et al. 2017 ("Attention Is All You Need"); Su et al. 2021 (RoFormer); Hoffmann et al. 2022 (Chinchilla); Dao et al. 2022 (FlashAttention).
9. **post-training**: supervised fine-tuning and instruction tuning, LoRA and QLoRA (rank, alpha, which matrices, memory saved), full fine-tuning versus adapters, catastrophic forgetting, data quality and mixing, RLHF with a reward model and PPO, DPO, GRPO, distillation.
   Reading: Hu et al. 2021 (LoRA); Dettmers et al. 2023 (QLoRA); Ouyang et al. 2022 (InstructGPT); Rafailov et al. 2023 (DPO); Shao et al. 2024 (DeepSeekMath, GRPO).
10. **inference-efficiency**: latency versus throughput, batching and continuous batching, PagedAttention, quantization (int8, int4, GPTQ, AWQ), pruning, distillation, speculative decoding, memory for weights and the KV cache, edge and mobile constraints (memory, power).
    Reading: Kwon et al. 2023 (vLLM, PagedAttention); Frantar et al. 2022 (GPTQ); Lin et al. 2023 (AWQ); Leviathan et al. 2023 (speculative decoding).
11. **rag-retrieval**: embeddings, bi-encoders versus cross-encoders, chunking, BM25 versus dense retrieval, hybrid search and reciprocal rank fusion, reranking, vector indexes (HNSW, IVF, product quantization), retrieval metrics (recall@k, MRR, nDCG), faithfulness of the generated answer, when retrieval beats fine-tuning.
    Reading: Lewis et al. 2020 (RAG); Karpukhin et al. 2020 (DPR); Malkov and Yashunin 2016 (HNSW); Es et al. 2023 (RAGAS).
12. **agents-tool-use**: function calling and tool schemas, structured output and constrained decoding, ReAct, planning and multi-step tasks, multi-agent patterns, memory, the Model Context Protocol, failure modes (wrong tool, bad arguments, loops), prompt injection and guardrails, evaluating agents.
    Reading: Yao et al. 2022 (ReAct); Schick et al. 2023 (Toolformer); the Model Context Protocol specification.
13. **recsys-ranking**: candidate generation and ranking stages, two-tower models, learning to rank (pointwise, pairwise, listwise; LambdaMART), features and leakage across time, position bias and click models, offline metrics (NDCG, MRR, recall@k) versus online results, interleaving and A/B tests, cold start, feedback loops and diversity.
    Reading: Burges 2010 ("From RankNet to LambdaRank to LambdaMART: An Overview"); Covington, Adams and Sargin 2016 (deep neural networks for YouTube recommendations); Joachims, Swaminathan and Schnabel 2017 (unbiased learning to rank with biased feedback); Yi et al. 2019 (sampling-bias-corrected two-tower retrieval).
14. **computer-vision**: convolutions and receptive fields, ResNet, vision transformers, transfer learning and fine-tuning, augmentation, detection and segmentation basics, metrics (IoU, mAP), contrastive image-text models.
    Reading: He et al. 2016 (ResNet); Dosovitskiy et al. 2020 (ViT); Ren et al. 2015 (Faster R-CNN); Radford et al. 2021 (CLIP).
15. **speech-audio**: features (log-mel, MFCC), voice activity detection, speaker embeddings (d-vector, x-vector), keyword spotting, ASR (CTC, RNN-T, attention encoder-decoder), streaming and latency, metrics (WER, EER, false accepts and false rejects).
    Reading: Graves et al. 2006 (CTC); Graves 2012 (RNN-T); Snyder et al. 2018 (x-vectors); Radford et al. 2022 (Whisper).
16. **data-sql**: SQL (joins, group by, window functions), pandas, Spark basics (partitions, shuffles, skew), data validation and quality checks, building training sets without leakage, feature stores, batch versus streaming pipelines.
    Practice: write the query or the job on a tiny table and state its cost.
