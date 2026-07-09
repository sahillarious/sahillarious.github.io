// Casper's knowledge base: everything the assistant is allowed to know about Sahil.
// This is injected as the (prompt-cached) system prompt. Keep it factual and current —
// when your resume changes, edit this file and redeploy. If it ever grows large enough
// that the whole thing shouldn't ride in every request, this is the seam where you'd
// swap the static string for a retrieval call (that's a contained change, not a rewrite).

export const KNOWLEDGE = `
# ABOUT SAHIL SAWANT

Sahil Sawant is an AI/ML Engineer with early-career experience building agentic AI
systems and multi-agent orchestration. He has delivered production AI platforms
including a PDF-to-Knowledge-Graph pipeline and a multi-agent troubleshooting platform,
leveraging LLM orchestration and graph-guided reasoning for real-time problem-solving
and knowledge management.

- Based in: Shrewsbury, MA, USA
- Open to relocation anywhere in the United States
- Currently looking for: AI Engineer, ML Engineer, Software Engineer, or Data Scientist roles

# CONTACT

- Email: sahilshivajisawant@gmail.com
- GitHub: https://github.com/sahillarious
- LinkedIn: https://www.linkedin.com/in/sahilsawant01/
- Resume: downloadable as a PDF from the portfolio site

# EXPERIENCE

## AI Research Assistant — University at Buffalo (Buffalo, NY) | Jun 2026 – Present
- Integrated a Neo4j knowledge graph with a Qdrant vector store (BGE-M3 dense + BM25
  hybrid search) into a single retrieval layer that runs both paths in parallel per
  question, allowing the university-hosted Qwen-27B model to answer queries across 450+
  scraped department pages with higher relevance.
- Cut median response latency from ~90s to ~45s by disabling Qwen's internal reasoning
  on Cypher generation while keeping it on for answer synthesis.
- Scraped and normalized HTML, Markdown, and JSONL from Playwright/Firecrawl crawls into
  a Neo4j graph, modeling faculties, courses, labs, research areas, and policies, which
  enabled students to run queries and quickly locate relevant information.
- Tech: Neo4j, Qdrant, BGE-M3, BM25, Qwen, Playwright, Firecrawl, hybrid search.

## AI Engineer — Arta Support (Remote) | Mar 2026 – May 2026
- Scaled a troubleshooting system into an enterprise platform with ~30s response latency
  by orchestrating 4 AI agent workflows (router, intent, clarification, diagnosis) powered
  by Claude Sonnet, optimizing production performance via Anthropic prompt-caching,
  Socket.IO tool-calling, and conditional self-correction retries.
- Paired Pinecone with Neo4j in a hybrid graph-guided RAG system, improving retrieval
  precision by 30% by landing agents directly on exact knowledge-graph nodes rather than
  relying on standard context-stuffing.
- Automated a PDF-to-Knowledge-Graph ingestion pipeline via Text-to-Cypher query
  generation, cutting knowledge-base update time by 40% and keeping vector indices
  synchronized with Neo4j.
- Deployed full-stack AWS authentication and LLM token-accounting systems (Cognito,
  DynamoDB, KMS, EC2), delivering role-based dashboards, self-serve API key rotation, and
  per-model usage tracking to enforce cross-region budget controls.
- Tech: Claude Sonnet, LangGraph, Neo4j, Pinecone, Socket.IO, AWS Cognito, DynamoDB, KMS, EC2.

## Analyst — Capgemini (Mumbai, India) | Dec 2022 – May 2024
- Engineered an enterprise text-to-SQL RAG system using LangGraph and Llama-2-70B over
  Oracle EBS schemas, enabling non-technical warehouse staff to query aerospace inventory
  databases in plain language.
- Slashed prompt token overhead by 65% and eliminated hallucinated column errors by
  abandoning static prompt definitions in favor of a dynamic retrieval mechanism that
  grounds generation on live, runtime SCM schema metadata.
- Improved the system to handle 5,000+ weekly inventory queries with a 94% user-acceptance
  accuracy rate, delivering a FastAPI backend and React frontend that stream verified SQL,
  raw data arrays, and generate analytical charts using Matplotlib.
- Tech: LangGraph, Llama-2-70B, Oracle EBS, FastAPI, React, Matplotlib.

# PROJECTS

## B.O.L.T — Behavioral Object Locomotion & Tracking
Real-time object detection and tracking with a custom-trained YOLOv8 model and Intel
RealSense depth estimation on a Jetson edge device, using a finite-state-machine
controller for closed-loop following on a Unitree Go2 quadruped. Extended with a
Whisper-based voice control pipeline supporting 20+ spoken commands.
Tech: YOLOv8, CNN, Computer Vision, Whisper STT, ROS/ROS2. GitHub: https://github.com/sahillarious/BOLT

## Buffalo Accident Risk & Resource Allocation
A PPO reinforcement-learning agent that learns optimal placement of Police, EMS, and DOT
resources across a 145-cell grid of Buffalo, NY, trained on ~10,000 annual traffic
incidents from the city's Open Data Portal. Reaches a reward of ~793 through strategic
resource clustering, versus -8,170 to -8,230 for a random baseline and ~-47,500 for a DQN agent.
Tech: PPO, Reinforcement Learning, PyTorch, Actor-Critic, Python.
GitHub: https://github.com/sahillarious/Buffalo-Accident-Risk-Prediction-Resource-Allocation

## DeepSpeech Therapy — Real-Time Voice AI Coach
A hierarchical deep learning pipeline for real-time speech therapy: a 1D convolutional
autoencoder flags faulty speech via MFCC reconstruction error (96.89% accuracy), while
CNN+Attention, Transformer, and ResNet18 architectures diagnose stuttering events like
blocks and prolongations (F1 0.67–0.70). A GPT-4 virtual coach turns diagnoses into
context-aware feedback, deployed through Gradio.
Tech: PyTorch, Autoencoders, Transformers, GPT-4, Gradio. GitHub: https://github.com/sahillarious/DeepSpeech

## End-to-End ML Pipeline — Job-Market Classification
Five-class job-category classifier at 87% accuracy built with PySpark on Databricks over
1.3M+ LinkedIn postings, deployed as a real-time SageMaker endpoint with Model Monitor for
data-drift detection. GitHub Actions CI/CD automates retrain-and-redeploy with model
versioning, validation gates, and a Streamlit prototype for interactive inference.
Tech: PySpark, Databricks, SageMaker, GitHub Actions, Streamlit.

## DermAI — AI-Powered Dermatology Assistant
An ensemble of ResNet50, DenseNet121, VGG-19, and EfficientNet-B0 classifying 7 skin
lesion types on the HAM10000 dataset, with SMOTE and class-weighted training to handle
severe class imbalance (6,705 vs. 115 samples across classes). The ensemble reaches 0.94
precision / 0.93 F1, up from 0.87 F1 for a single ResNet50 baseline. A GPT-4 feedback layer
turns classifications into context-aware diagnostic explanations via Gradio.
Tech: PyTorch, ResNet50, EfficientNet-B0, SMOTE, GPT-4, Gradio. GitHub: https://github.com/sahillarious/DermAI

# SKILLS

- Languages & Libraries: Python, PySpark, SQL / PL-SQL, TensorFlow, PyTorch, Scikit-Learn,
  Pandas, NumPy, SciPy, Matplotlib, Seaborn, spaCy, NLTK
- GenAI & ML: LangGraph, LangChain, RAG Systems, Agentic Workflows, MCP,
  Agent-to-Agent Communication, LLM Orchestration, Prompt Engineering, Hugging Face,
  CNNs, RNNs, LSTMs, Transformers, Supervised & Unsupervised Learning
- MLOps & Deployment: Amazon SageMaker, SageMaker Model Monitor, CI/CD (GitHub Actions),
  Model Deployment, Model Monitoring / Drift Detection, Model Versioning, Streamlit
- Backend & Frontend: FastAPI, Node.js, React, Socket.IO, REST APIs, Git, Linux/Unix
- Databases & Cloud: Neo4j, Qdrant, Pinecone, DuckDB, AWS, GCP, Azure, Docker,
  Apache Spark, Oracle EBS

# EDUCATION

- Master of Science in Artificial Intelligence — University at Buffalo, SUNY
  (Buffalo, NY, Aug 2024 – Dec 2025). Coursework: Machine Learning, Deep Learning,
  Computer Vision, Analysis of Algorithms.
- Bachelor of Engineering in Electronics & Telecommunication — University of Mumbai
  (Mumbai, India, Aug 2018 – May 2022). Coursework: Database Management Systems, Image Processing.

# ACHIEVEMENTS

- Winner, AI For Good Hackathon (Spring 2025) — an AI-driven snow management solution using LSTM models.
- Best Student Volunteer of the Standing Committee, IEEE Bombay Section (2022).
- Winner, IEEE R10 Connect Logo Design Competition (IEEE Asia-Pacific region).

# VOLUNTEERING

- Design Lead, IEEE Education Society Young Professionals Team (2024)
- Secretary, IEEE Bombay Section Young Professionals (2023)
- Design Lead, IEEE Bombay Section Student Activities Team (2022)
`;
