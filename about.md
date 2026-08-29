# LLM Knowledge Bases Explained

Andrej Karpathy is someone whose content I personally enjoy consuming. He was the director of AI at Tesla doing computer vision work with regards to Autopilot and also a founding member of OpenAI. His YouTube channel is also pretty awesome where he teaches deep learning not just to professionals but also the general public.

Not so long ago he posted on X about a new idea of leveraging LLMs to build personal knowledge bases. You use LLMs to reason and synthesize information across documents as well for answering queries. He gave a cool analogy to tie these ideas together:

## The Compiler Analogy

If you have coded before, you know how programs are run: humans write source code in a language (Python, Java, etc.), which is then run through a compiler or interpreter to get executable code that the machine can understand. Applying this to a knowledge base:

- **Raw documents** (research papers, notes, articles, etc.) $\rightarrow$ **Source Code**: This is the raw, messy, and unstructured information.
- **The LLM** $\rightarrow$ **The Compiler**: It takes the raw documents and compiles them into something it can understand and reason over.
- **The Wiki** $\rightarrow$ **Executable Code**: Created by the LLM, this is structured to store entities, topics, and generated overviews/summaries of the data.

The idea is simple: based on raw documents, the LLM generates/updates a wiki and uses it to answer queries, while the raw documents remain unchanged. The wiki documents contain references to entities and topics, helping the LLM read across multiple documents. Karpathy noted that feeding outputs back into the knowledge base allows for compounding knowledge over time. He also mentioned the importance of periodic **health checks** to identify contradictions, gaps, or inconsistencies.

## Comparison with RAG

You may be familiar with **RAG (Retrieval Augmented Generation)**. RAG chunks documents, converts them to vectors using an embedding model, and stores them in a vector database. During a query, similarity search retrieves relevant chunks to inject into the LLM's context.

The issue with RAG is that it is fragmented, providing a **local rather than a global understanding** of the data. There is also the risk of not retrieving the necessary chunks at all. The wiki-based approach is more agentic and structured for better LLM comprehension.

## Potential Downsides

- **Scalability**: This approach works well for ~100 documents but may not scale beyond that. LLM performance tends to degrade as context increases, even before reaching the limit.
- **Loss of Detail**: Since the wiki consists of summaries and overviews, subtle details present in the raw sources might be lost.

## About This Project

I found this idea fascinating and decided to implement it. You can clone this repository into an agentic IDE (such as Claude Code, OpenCode, or Antigravity) to use it. To get the most out of this setup, I recommend using **Obsidian**, a free note-taking application with a Web Clipper extension that converts web articles into markdown files.

To make the knowledge base actionable, I added a **quiz component** that generates multiple-choice questions on a topic of your interest to test your understanding and give you feedback based on the quiz results.