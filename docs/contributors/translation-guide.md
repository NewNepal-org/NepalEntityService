# Translation Guide

The Nepal Entity Service provides powerful translation capabilities between English and Nepali, supporting both Devanagari script and Romanized Nepali text.

## Overview

The translation service uses AWS Bedrock (Claude Sonnet 4.5) to provide:

- **English ↔ Nepali Translation**: High-quality translation between languages
- **Devanagari Support**: Native Nepali script translation
- **Romanized Nepali**: Handles transliterated Nepali text (e.g., "Ma bhat khanchu")
- **Auto-Detection**: Automatically detects source language
- **Transliteration**: Provides romanized versions of Nepali text

## Quick Start

### Basic Translation

Translate English to Nepali:

```bash
nes translate --to ne "Ram Chandra Poudel"
```

Output:
```
Detected language: English

Translation: राम चन्द्र पौडेल
Transliteration: Ram Chandra Paudel
```

Translate Nepali to English:

```bash
nes translate --to en "राम चन्द्र पौडेल"
```

Output:
```
Detected language: Nepali

Translation: Ram Chandra Poudel
```

### Romanized Nepali

The translator handles Romanized Nepali text:

```bash
nes translate --to en "Ma bhat khanchu."
```

Output:
```
Translation: I eat rice.
```

## Configuration

### Environment Variables

Configure the translation service using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for Bedrock | `us-east-1` |
| `AWS_BEDROCK_MODEL_ID` | Model ID to use | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| `AWS_PROFILE` | AWS profile name | (uses default) |
| `AWS_ACCESS_KEY_ID` | AWS access key | (uses default credential chain) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | (uses default credential chain) |

### AWS Credentials

The translation service requires AWS credentials with Bedrock access. Configure credentials using one of these methods:

1. **Environment Variables**:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=us-east-1
   ```

2. **AWS Credentials File** (`~/.aws/credentials`):
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   ```

3. **AWS Profile**:
   ```bash
   export AWS_PROFILE=my-profile
   nes translate --to ne "Hello"
   ```

4. **IAM Role** (when running on AWS infrastructure)

## CLI Reference

### Command Syntax

```bash
nes translate [OPTIONS] [TEXT]
```

### Options

| Option | Description |
|--------|-------------|
| `--from [en\|ne]` | Source language (auto-detected if not specified) |
| `--to [en\|ne]` | Target language (required) |
| `--provider [aws]` | LLM provider to use (default: aws) |
| `--model TEXT` | Model ID to use (env: AWS_BEDROCK_MODEL_ID) |
| `--region TEXT` | AWS region (env: AWS_REGION) |
| `--help` | Show help message |

### Examples

**Basic translation:**
```bash
nes translate --to ne "Ram Chandra Poudel"
```

**Specify source language:**
```bash
nes translate --from en --to ne "Ram Chandra Poudel"
```

**Use different region:**
```bash
nes translate --region us-west-2 --to ne "Hello"
```

**Read from stdin:**
```bash
echo "Ram Chandra Poudel" | nes translate --to ne
```

**Translate file content:**
```bash
cat names.txt | nes translate --to ne
```

## Use Cases

### Translating Names

Translate Nepali names to English:

```bash
nes translate --to en "राम चन्द्र पौडेल"
# Output: Ram Chandra Poudel

nes translate --to en "पुष्प कमल दाहाल"
# Output: Pushpa Kamal Dahal
```

Translate English names to Nepali:

```bash
nes translate --to ne "Ram Chandra Poudel"
# Output: राम चन्द्र पौडेल
```

### Translating Political Terms

```bash
nes translate --to en "राष्ट्रपति"
# Output: President

nes translate --to en "प्रधानमन्त्री"
# Output: Prime Minister

nes translate --to en "संसद"
# Output: Parliament
```

### Batch Translation

Translate multiple items using a shell script:

```bash
#!/bin/bash
# translate_names.sh

names=(
    "राम चन्द्र पौडेल"
    "पुष्प कमल दाहाल"
    "केपी शर्मा ओली"
)

for name in "${names[@]}"; do
    echo -n "$name -> "
    nes translate --to en "$name" | grep "Translation:" | cut -d: -f2
done
```

### Mixed Language Text

Handle text with both English and Romanized Nepali:

```bash
nes translate --to en "Ram Chandra Paudel Nepal ko rashtrapati hun."
# Output: Ram Chandra Poudel is the President of Nepal.
```

## Language Detection

The translator automatically detects the source language based on script:

- **Devanagari characters** → Detected as Nepali (`ne`)
- **Latin characters** → Detected as English (`en`)

When auto-detection is used, the output shows the detected language:

```bash
nes translate --to en "राम चन्द्र पौडेल"
```

Output:
```
Detected language: Nepali

Translation: Ram Chandra Poudel
```

## Transliteration

When translating from Nepali to English, the service provides transliteration (romanized version):

```bash
nes translate --to en "राम चन्द्र पौडेल"
```

Output:
```
Detected language: Nepali

Translation: Ram Chandra Poudel
Transliteration: Ram Chandra Paudel
```

## Best Practices

### 1. Use Explicit Source Language for Consistency

While auto-detection works well, specify the source language for consistent results:

```bash
nes translate --from ne --to en "राम चन्द्र पौडेल"
```

### 2. Set Environment Variables for Configuration

Instead of passing options every time, set environment variables:

```bash
export AWS_REGION=us-west-2
export AWS_BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

nes translate --to ne "Hello"
```

### 3. Use Pipes for Batch Processing

Process multiple lines efficiently:

```bash
cat names.txt | while read line; do
    nes translate --to en "$line"
done
```

### 4. Handle Errors Gracefully

Check exit codes in scripts:

```bash
if nes translate --to ne "Hello" > /dev/null 2>&1; then
    echo "Translation successful"
else
    echo "Translation failed"
fi
```

## Troubleshooting

### Error: Failed to initialize translation service

**Cause**: AWS credentials not configured or insufficient permissions.

**Solution**:
1. Verify AWS credentials are set up correctly
2. Ensure the IAM user/role has Bedrock access
3. Check the AWS region supports Bedrock

### Error: Unsupported model

**Cause**: The specified model ID is not supported.

**Solution**: Use the default model or check available models in your AWS region.

### Empty or incorrect translations

**Cause**: Input text may be ambiguous or the model may need more context.

**Solution**:
1. Specify the source language explicitly with `--from`
2. Ensure the input text is clear and well-formed
3. Try breaking complex sentences into smaller parts

### Slow performance

**Cause**: Network latency or AWS Bedrock API response time.

**Solution**:
1. Use a region closer to your location
2. Process translations in batches when possible
3. Consider caching frequently translated terms

## Programmatic Usage

For programmatic access to translation features, see the [Scraping Service Guide](scraping-service-guide.md) or the Jupyter notebook at `notebooks/05_translation_service.ipynb`.

## Related Documentation

- [Contributor Guide](contributor-guide.md)
- [Scraping Service Guide](scraping-service-guide.md)
- [Usage Examples](usage-examples.md)
