# Generate Optimized Prompt

Generate a high-quality, optimized prompt following Claude & Claude Code best practices.

**Reference**: Based on best practices from `@docs/meta/claude_prompting.md`

## Instructions

## Task Requirements

**Generate an optimized prompt for:** $ARGUMENTS

<thinking>
First, I'll analyze the requirements:
- Identify if this task needs chain-of-thought, examples, structure, or specific techniques
- Determine optimal prompt structure based on complexity
- Select appropriate best practices for this specific use case
</thinking>

Follow these mandatory requirements:

### 1. Structure & Organization

- Use XML tags to organize different sections (`<instructions>`, `<context>`, `<examples>`, `<constraints>`)
- Place data/context BEFORE instructions (30% quality improvement)
- Use numbered steps for multi-part tasks
- Define clear success criteria upfront

### 2. Essential Components to Include

#### For Complex/Reasoning Tasks:

```xml
<thinking>
Step-by-step reasoning process
</thinking>

<answer>
Final response
</answer>
```

#### For Code/Technical Tasks:

- Specify exact requirements with numbered steps
- Include error handling instructions
- Add: "If unsure about implementation details, write 'I need clarification on...'"

#### For Data Processing:

- Place the data first, instructions last
- Use templates with `{{variables}}` for reusability
- Specify output format explicitly

### 3. Examples Section (if applicable)

Include 3-5 concrete examples when:

- The task involves format transformation
- There are edge cases to handle
- The pattern isn't immediately obvious

Format:

```xml
<examples>
Input: [specific input]
Output: [expected output]
</examples>
```

### 4. Constraints & Error Handling

Always include:

- "If you are unsure, write 'I don't know'" (improves accuracy)
- Specific constraints or limitations
- What NOT to do (as important as what to do)

### 5. For Claude Code Specific Tasks:

- Break into numbered action steps
- Specify tool usage preferences (parallel vs sequential)
- Include verification steps (tests, linting, type checking)
- Add: "Use TodoWrite to track progress" for complex multi-step tasks

### 6. Performance Optimizations:

- Remove redundant instructions
- Use concise, imperative language
- Batch related operations
- Specify parallel execution where applicable

### 7. Output Format:

Specify the desired output format:

- Code block with language
- Structured data (JSON, XML, Markdown)
- Natural language with specific tone
- File modifications with exact paths

### Template Structure:

```xml
<context>
[Background information if needed]
[Data to process - place before instructions]
</context>

<instructions>
[Clear, numbered steps if multiple]
[Specific requirements]
</instructions>

<examples>
[3-5 concrete examples if pattern-based]
</examples>

<constraints>
- If unsure, write "I don't know"
- [Specific limitations]
- [What to avoid]
</constraints>

<thinking>
[For complex reasoning tasks]
</thinking>

<answer>
[Final deliverable format]
</answer>
```

### Key Insights from @docs/meta/claude_prompting.md

#### Core Principles

1. **Be Clear and Direct** - Specificity yields better results  
2. **Use Structure** - XML tags, numbered steps, templates
3. **Provide Examples** - 3-5 examples reduce errors by 60%
4. **Enable Reasoning** - Chain of thought improves quality by 39%

#### Proven Techniques

- **XML Tags for Organization** - Use `<instructions>`, `<context>`, `<examples>`, `<thinking>`, `<answer>`
- **Data-First Approach** - Place data/context before instructions for 30% quality improvement
- **Chain of Thought** - Use `<thinking>` tags for step-by-step reasoning
- **Few-Shot Examples** - Include 3-5 examples for pattern-based tasks

#### Claude Code Specific

- **Be Specific on First Attempt** - Detailed initial prompts get better results
- **Numbered Steps for Complex Tasks** - Break down into systematic steps
- **Parallel Operations** - Use "Simultaneously:" for independent tasks

#### Quick Wins

- Add "If unsure, say 'I don't know'" - improves accuracy
- Use XML tags liberally - navigation markers for Claude
- One high-quality example - reduces format errors by 60%
- Start with data, end with instructions - 30% quality boost

### Quality Checklist:

- [ ] Uses XML tags for structure
- [ ] Data placed before instructions (if applicable)
- [ ] Includes uncertainty handling
- [ ] Has numbered steps for complex tasks
- [ ] Provides examples for pattern-based tasks
- [ ] Specifies success criteria
- [ ] Clear about output format
- [ ] Includes role setting if beneficial
- [ ] Enables chain-of-thought for reasoning tasks
- [ ] Avoids over-prompting for simple tasks

### Common Pitfalls to Avoid:

1. Over-prompting simple tasks
2. Vague instructions without success criteria
3. Missing examples for format transformations
4. No uncertainty handling
5. Instructions before large data blocks
6. Sequential operations that could be parallel
7. Missing output format specification

## Generate the Optimized Prompt

Generate the optimized prompt following ALL these best practices. The prompt should be immediately usable and achieve >95% accuracy for the specified task.

### Save the Generated Prompt

After generating the prompt:

1. **Extract a command name** from the user's requirements (e.g., if they ask for "a prompt to refactor code", use `refactor-code`)
2. **Create a new command file** at `.claude/commands/[command-name].md`
3. **Format the saved prompt** as a ready-to-use Claude command:
   - Add a descriptive title as an H1 header
   - Include a brief description of what the command does
   - Place the generated prompt content directly (without wrapping in code blocks)
   - Ensure it's immediately executable when selected from the command menu

**Example saved command structure:**

```markdown
# [Command Title]

[Brief description of what this command does]

[The generated prompt content - ready to execute]
```

4. **Inform the user** that the prompt has been saved and can be accessed via the command menu

### Output Format

1. First, display the generated prompt to the user
2. Then save it as a command file
3. Confirm the save location: `.claude/commands/[command-name].md`
