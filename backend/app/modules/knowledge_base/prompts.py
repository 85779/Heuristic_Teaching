"""RAG prompt templates for the knowledge base module.

Contains templates for enriching hints with retrieved knowledge chunks.
"""

# Hint enrichment template for generating student-facing hints
HINT_ENRICHMENT_TEMPLATE = """你是一位高中数学辅导老师。根据以下知识点，为学生生成解题提示：

【相关知识点】
{chunk_1}
---
{chunk_2}
---
{chunk_3}

【学生当前步骤】
{student_input}

【期望的下一步】
{expected_step}

请生成一个温和、有启发性的提示，引导学生自己发现答案。
"""

# Alternative template with fewer chunks
HINT_ENRICHMENT_TEMPLATE_SHORT = """你是一位高中数学辅导老师。根据以下知识点，为学生生成解题提示：

【相关知识点】
{chunk_1}

【学生当前步骤】
{student_input}

【期望的下一步】
{expected_step}

请生成一个温和、有启发性的提示，引导学生自己发现答案。
"""

# System prompt for RAG retrieval
RAG_SYSTEM_PROMPT = """你是一个高中数学知识库助手。你的任务是帮助学生和教师检索相关的数学知识点、解题方法和教学策略。

你可以检索以下类型的知识：
- 知识点（knowledge_point）：核心数学概念和性质
- 解题方法（method）：特定的解题技巧和步骤
- 数学概念（concept）：基础概念的定义和解释
- 典型例题（example）：包含详细解答的例题
- 教学策略（strategy）：教学方法和建议

请根据用户的查询，返回最相关的知识内容。
"""

# Template for building context from chunks
CONTEXT_BUILDING_TEMPLATE = """【相关知识片段 {index}】
类型：{doc_type}
标题：{name}
内容：{content}

"""

# Query expansion template for better retrieval
QUERY_EXPANSION_TEMPLATE = """将以下查询扩展为更详细的检索查询，包含可能的同义词和相关概念：

原始查询：{query}

请生成一个扩展的、优化的检索查询。
"""


def format_hint_enrichment(
    chunks: list,
    student_input: str,
    expected_step: str
) -> str:
    """Format the hint enrichment template with chunk data.
    
    Args:
        chunks: List of KGChunk objects.
        student_input: Student's current input/step.
        expected_step: Expected next step content.
    
    Returns:
        Formatted prompt string.
    """
    # Fill in chunks
    chunk_contents = []
    for i, chunk in enumerate(chunks[:3]):  # Max 3 chunks
        chunk_text = chunk.content[:500]  # Truncate long content
        chunk_contents.append(f"【知识片段 {i+1}】\n{chunk_text}")
    
    # Pad with empty strings if fewer than 3 chunks
    while len(chunk_contents) < 3:
        chunk_contents.append(f"【知识片段 {len(chunk_contents)+1}】\n（未找到相关知识）")
    
    chunk_1 = chunk_contents[0] if len(chunk_contents) > 0 else ""
    chunk_2 = chunk_contents[1] if len(chunk_contents) > 1 else ""
    chunk_3 = chunk_contents[2] if len(chunk_contents) > 2 else ""
    
    return HINT_ENRICHMENT_TEMPLATE.format(
        chunk_1=chunk_1,
        chunk_2=chunk_2,
        chunk_3=chunk_3,
        student_input=student_input,
        expected_step=expected_step
    )


def format_context_from_chunks(chunks: list) -> str:
    """Build a context string from retrieved chunks.
    
    Args:
        chunks: List of KGChunk objects.
    
    Returns:
        Formatted context string.
    """
    context_parts = []
    
    for i, chunk in enumerate(chunks):
        metadata = chunk.metadata or {}
        doc_type = metadata.get("type", "unknown")
        name = metadata.get("name", f"片段 {i+1}")
        
        context_parts.append(CONTEXT_BUILDING_TEMPLATE.format(
            index=i + 1,
            doc_type=doc_type,
            name=name,
            content=chunk.content
        ))
    
    return "\n".join(context_parts)


# Export all templates
RAG_PROMPTS = {
    "hint_enrichment": HINT_ENRICHMENT_TEMPLATE,
    "hint_enrichment_short": HINT_ENRICHMENT_TEMPLATE_SHORT,
    "system": RAG_SYSTEM_PROMPT,
    "context_building": CONTEXT_BUILDING_TEMPLATE,
    "query_expansion": QUERY_EXPANSION_TEMPLATE,
    "format_hint_enrichment": format_hint_enrichment,
    "format_context_from_chunks": format_context_from_chunks,
}
