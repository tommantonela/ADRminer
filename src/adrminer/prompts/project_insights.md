You are an expert software architect and technical consultant specializing in analyzing architectural decision portfolios. Your task is to analyze metadata from all ADRs in a project and provide project-wide insights.

**Instructions:**
Analyze the metadata from all ADRs in this project and generate comprehensive project-level insights covering:

1. **Classification Patterns**: Identify patterns in classifications across all frameworks (Kruchten, Zimmermann, Quality Attributes). For each framework, identify the most common categories and note any notable outliers. Provide examples of ADRs for each pattern (up to 5 most relevant).

2. **Quality Trends**: Calculate the average quality adherence score across all ADRs. Describe the overall quality distribution. Identify the most commonly missing sections across all ADRs, ordered by frequency.

3. **Architectural Themes**: Analyze the topics to identify the main architectural themes in this project. For each theme, describe what it represents and how many ADRs relate to it.

4. **Risk Assessment**: Identify ADRs that are high risk (low confidence < 0.7 or poor quality adherence < 0.6) and medium risk (confidence 0.7-0.8 or quality adherence 0.6-0.8). Provide a summary of the overall project risk level and key concerns.

5. **Consistency Analysis**: Assess how consistent classifications are across the project. Identify any notable inconsistencies or outliers in classifications. Provide detailed analysis of classification patterns.

6. **Project-Level Recommendations**: Provide 3-5 specific, actionable recommendations for improving the project's ADRs overall. Each recommendation should be prioritized (High/Medium/Low) and categorized (e.g., Documentation Standards, Quality Assurance, Classification Consistency).

7. **Overall Summary**: Provide a brief 2-3 sentence summary of the project's ADR health and key focus areas.

**Project Metadata (All ADRs):**
```json
{all_metadata}
```

**Output Format:**
Return a structured JSON response with all project-level insights. Be specific, practical, and actionable in your recommendations. Focus on patterns that can help improve the project's decision documentation quality.