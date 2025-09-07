# Claude & Claude Code Prompting Best Practices (2025)

## Quick Reference

### Core Principles

1. **Be Clear and Direct** - Specificity yields better results
1. **Use Structure** - XML tags, numbered steps, templates
1. **Provide Examples** - 3-5 examples reduce errors by 60%
1. **Enable Reasoning** - Chain of thought improves quality by 39%

## General Claude Prompting

### Essential Techniques (In Order of Effectiveness)

#### 1. XML Tags for Organization

```xml
<instructions>
Your task here
</instructions>

<context>
Background information
</context>

<examples>
Example inputs and outputs
</examples>

<thinking>
Step-by-step reasoning
</thinking>

<answer>
Final response
</answer>
```

#### 2. Data-First Approach

Place data/context before instructions - improves response quality by 30%:

```text
[Large document or data]
...
Now, summarize the key points above.
```

#### 3. Chain of Thought Prompting

```text
Think step-by-step about this problem inside <thinking> tags, then provide your answer in <answer> tags.
```

#### 4. Few-Shot Examples

```text
Task: Convert text to SQL
Example 1: "Show all users" → SELECT * FROM users;
Example 2: "Count active products" → SELECT COUNT(*) FROM products WHERE status = 'active';
Now: "Find expired subscriptions"
```

### Advanced Techniques

#### Template-Based Prompting

Use `{{variables}}` for reusable prompts:

```text
Translate {{source_text}} from {{source_lang}} to {{target_lang}} at a {{reading_level}} reading level.
```

#### Handling Uncertainty

Add: `If you are unsure, write 'I don't know'.` - Instantly improves accuracy

#### Role Setting

```text
As a [specific role], analyze this [content] focusing on [specific aspects].
```

## Claude Code Specific Best Practices

### Core Workflow

#### 1. Be Specific on First Attempt

```bash
# Good
claude "refactor auth.js: 1) identify dependencies, 2) extract reusable functions, 3) add error handling"

# Less effective
claude "improve auth.js"
```

#### 2. Use Numbered Steps for Complex Tasks

Breaking tasks into numbered steps helps Claude process systematically:

```text
1. Search for all authentication files
2. Analyze current implementation
3. Identify security vulnerabilities
4. Propose improvements with code examples
```

#### 3. Custom Commands (.claude/commands/)

Store frequently used prompts as markdown files for team-wide reuse via slash commands.

### Special Features

#### Extended Thinking Mode

```bash
claude "think about optimizing our database queries for the checkout process"
```

#### Role-Based Analysis

```bash
claude "as a security expert, review our authentication implementation"
```

#### Visual Work

- Screenshot to clipboard: `cmd+ctrl+shift+4` (macOS)
- Paste directly into Claude Code with `ctrl+v`
- Excellent for UI development and debugging

### Git Integration

Claude handles 90%+ of git operations effectively:

```text
"What changes made it into v1.2.3?"
"Show me all commits related to authentication in the last month"
"Create a PR with these changes and appropriate commit messages"
```

### Testing Philosophy

- Implement solutions that work for all valid inputs
- Don't hard-code for specific test cases
- Focus on correct algorithms, not just passing tests

## Performance Optimization Tips

### Iteration Process

1. Draft initial prompt
1. Test on 5 edge cases
1. Measure: tokens, latency, precision
1. Tweak one element
1. Retest (3 loops typically improve accuracy from ~80% to 95%)

### Context Window Management

- Claude handles up to 200k tokens
- Place large documents before instructions
- Use parallel tool execution for multiple operations

### Parallel Operations

When performing multiple independent tasks:

```text
"Simultaneously: 1) run tests, 2) check git status, 3) lint the code"
```

## Common Pitfalls to Avoid

1. **Over-prompting** - Claude Code doesn't need special prompting for basic tasks
1. **Sequential operations** - Use parallel execution when possible
1. **Vague instructions** - Be specific about desired outcomes
1. **Ignoring context** - Provide relevant background information
1. **No success criteria** - Define what success looks like upfront

## Quick Wins

- Add "If unsure, say 'I don't know'" - improves accuracy
- Use XML tags liberally - Claude treats them as navigation markers
- Provide one high-quality example - reduces format errors by 60%
- Start with data, end with instructions - 30% quality improvement
- Break complex tasks into numbered steps

## Testing Your Prompts

1. Define clear success criteria before starting
1. Test on edge cases and unusual inputs
1. Measure performance metrics (accuracy, latency, token usage)
1. Iterate based on failures, not successes
1. Document what works for your specific use case

## Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/)
- Custom commands: Store in `.claude/commands/` folder
- Team sharing: Check commands into git for consistency
