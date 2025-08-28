# Galileo AI Integration Guide

## Overview

The Thinking Graph application integrates with [Galileo AI](https://www.rungalileo.io/) to provide enterprise-grade AI monitoring, evaluation, and observability capabilities. This integration enables comprehensive tracking of AI interactions, reasoning quality assessment, and performance analytics.

## 🌟 Key Features

### Advanced AI Monitoring
- **Real-time conversation tracking**: Every user-AI interaction is logged and evaluated
- **Reasoning quality assessment**: Multi-dimensional scoring across coherence, completeness, clarity, and relevance
- **Knowledge graph performance monitoring**: Track how effectively the system builds and maintains knowledge connections
- **Session-based analytics**: Detailed insights into conversation flows and user engagement patterns

### Evaluation Metrics
- **Reasoning Quality Score**: 0-1 scale evaluation of AI response quality
- **Coherence Analysis**: How well responses connect logically
- **Completeness Assessment**: Whether responses adequately address user queries
- **Clarity Measurement**: How understandable and well-structured responses are
- **Relevance Scoring**: How well responses relate to the user's actual needs

### Enterprise-Grade Observability
- **Interactive dashboards**: Beautiful, real-time visualization of AI performance
- **Trend analysis**: Track improvement/degradation patterns over time
- **Comparative analytics**: Benchmark performance across different conversation types
- **Export capabilities**: Data extraction for further analysis and reporting

## 🔧 Architecture

### Backend Integration
The `GalileoService` class (`backend/services/galileo_service.py`) provides:

```python
class GalileoService:
    def get_reasoning_response_with_evaluation(self, user_message, session_id)
    def health_check(self)
    def log_interaction(self, interaction_data)
```

### Key Integration Points
1. **Chat Processing**: Every `/api/chat` request includes Galileo evaluation
2. **Health Monitoring**: `/health` endpoint reports Galileo service status
3. **Fallback Support**: Graceful degradation when Galileo is unavailable
4. **Configurable Logging**: Environment-variable controlled integration depth

## 📋 Setup Instructions

### 1. Galileo Account Setup
1. Visit [https://www.rungalileo.io/](https://www.rungalileo.io/)
2. Sign up for an account
3. Create a new project for your Thinking Graph application
4. Generate API keys from the dashboard

### 2. Environment Configuration
Update your `.env` file with Galileo credentials:

```env
# Galileo AI Evaluation Platform
GALILEO_API_KEY=your_galileo_api_key_here
GALILEO_PROJECT=vizbrain-thinking-graph
GALILEO_LOG_STREAM=vizbrain-chat-logs
GALILEO_CONSOLE_URL=https://app.galileo.ai
ENABLE_GALILEO_MONITORING=true
```

### 3. Verify Integration
Start your application and check the health endpoint:

```bash
curl http://localhost:8000/health
```

Look for `galileo_service` status in the response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-XX...",
  "kg_system_initialized": true,
  "galileo_service": {
    "status": "connected",
    "enabled": true,
    "service_version": "1.0.0"
  }
}
```

## 🚀 Usage

### Automatic Monitoring
Once configured, Galileo monitoring works automatically:
- Every chat message is evaluated and logged
- Reasoning quality scores are generated in real-time
- Performance metrics are continuously updated
- No additional code changes required

### Manual Logging
For custom interactions, use the service directly:

```python
from services.galileo_service import get_galileo_service

galileo_service = get_galileo_service()
thoughts, response, evaluation = galileo_service.get_reasoning_response_with_evaluation(
    user_message="How does knowledge graph construction work?",
    session_id="session_123"
)
```

### Accessing Analytics
1. Visit your Galileo dashboard at [https://app.galileo.ai](https://app.galileo.ai)
2. Navigate to your project
3. View real-time analytics and historical trends
4. Export data for custom analysis

## 🔄 Graceful Fallback

### When Galileo is Unavailable
The system automatically falls back to basic evaluation:
- **Self-evaluation metrics**: Simple quality scoring based on response characteristics
- **Local logging**: Interaction tracking without external dependencies
- **Continued functionality**: All core features remain operational

### Fallback Indicators
```json
{
  "evaluation": {
    "galileo_enabled": false,
    "evaluation_scores": {
      "reasoning_quality": 0.85,
      "response_length_score": 0.9,
      "complexity_score": 0.8
    },
    "self_evaluation": {
      "method": "basic_fallback",
      "confidence": "medium"
    }
  }
}
```

## 📊 Analytics Dashboard

### Available Metrics
- **Response Quality Trends**: Track improvement over time
- **User Engagement Patterns**: Analyze conversation flow and duration
- **Knowledge Graph Growth**: Monitor entity and relationship extraction
- **Performance Benchmarks**: Compare against baseline metrics

### Custom Analytics
Extend the integration with custom metrics:
1. Modify `galileo_service.py` to include additional data points
2. Update logging calls to include domain-specific metadata
3. Create custom dashboards in the Galileo console

## 🔍 Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
Error: Galileo API authentication failed
```
- Verify your `GALILEO_API_KEY` is correct
- Check that your project settings match the configuration
- Ensure your account has sufficient permissions

**2. Connection Timeouts**
```bash
Warning: Galileo service timeout, falling back to local evaluation
```
- Check network connectivity
- Verify Galileo service status
- Increase timeout values if needed

**3. Missing Data**
- Ensure `ENABLE_GALILEO_MONITORING=true` in your environment
- Verify the service is properly initialized on startup
- Check application logs for integration warnings

### Debug Mode
Enable detailed logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Health Check Verification
Regular health monitoring:
```bash
# Automated health check
curl -s http://localhost:8000/health | jq '.galileo_service'
```

## 🎯 Best Practices

### Performance Optimization
- Use session-based logging to reduce API calls
- Implement local caching for frequently accessed evaluations
- Batch log uploads during low-traffic periods

### Security Considerations
- Store API keys securely in environment variables
- Use HTTPS endpoints for production deployments
- Regularly rotate API keys and credentials

### Monitoring Strategy
- Set up alerts for service degradation
- Monitor evaluation score trends for quality insights
- Regularly review and optimize logging frequency

## 🔮 Advanced Features

### Custom Evaluation Criteria
Extend evaluation with domain-specific metrics:
```python
custom_evaluation = {
    'domain_expertise': evaluate_domain_knowledge(response),
    'factual_accuracy': check_facts(response),
    'citation_quality': validate_sources(response)
}
```

### Integration with Knowledge Graph
Monitor graph construction quality:
```python
kg_metrics = {
    'entities_extracted': len(entities),
    'relationships_created': len(relationships),
    'graph_coherence_score': calculate_coherence(graph_data)
}
```

---

## 📚 Additional Resources

- [Galileo AI Documentation](https://docs.rungalileo.io/)
- [API Reference](https://api-docs.rungalileo.io/)
- [Best Practices Guide](https://www.rungalileo.io/best-practices)
- [Community Forum](https://community.rungalileo.io/)

---

*The thinking-graph project now provides enterprise-grade AI monitoring and evaluation capabilities through Galileo AI integration, ensuring transparent, measurable, and continuously improving AI interactions.*