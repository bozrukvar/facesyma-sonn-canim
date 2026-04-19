"""
Optimized LLM Configuration for Server Deployment
GPU acceleration, batching, caching, and performance tuning
"""
import os
from typing import Dict, Any, Optional
import logging

log = logging.getLogger(__name__)

class LLMConfig:
    """Optimized LLM configuration for production"""

    def __init__(self, deployment_env: str = "server"):
        """
        deployment_env: 'local' (CPU), 'server' (GPU), 'cloud' (API)
        """
        self.deployment_env = deployment_env
        self.config = self._get_optimal_config()

    def _get_optimal_config(self) -> Dict[str, Any]:
        """Get optimal config based on deployment environment"""
        if self.deployment_env == "server":
            return self._server_config()
        elif self.deployment_env == "cloud":
            return self._cloud_config()
        else:
            return self._local_config()

    def _server_config(self) -> Dict[str, Any]:
        """GPU-accelerated server configuration"""
        return {
            "model": {
                "name": "mistral",
                "quantization": "q4_k_m",  # 4-bit quantization for speed
                "gpu_memory": "24GB",  # For A100/H100 GPUs
                "num_gpu": 2,  # Multi-GPU support
                "tensor_parallel": True  # Distributed inference
            },
            "inference": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "num_ctx": 4096,
                "num_predict": 512,
                "num_keep": 0,
                "num_threads": 32,  # CPU threads for non-GPU ops
                "batch_size": 32  # Process 32 requests simultaneously
            },
            "performance": {
                "enable_gpu": True,
                "enable_batching": True,
                "enable_kv_cache": True,  # Key-Value caching
                "enable_flash_attention": True,  # Fast attention
                "max_queue_size": 1000,
                "request_timeout": 30,  # seconds
                "model_cache_size": "48GB"
            },
            "optimization": {
                "enable_compilation": True,
                "enable_gradient_checkpointing": False,
                "precision": "float16",  # Half precision for speed
                "use_rope_scaling": True
            }
        }

    def _cloud_config(self) -> Dict[str, Any]:
        """Cloud API configuration (OpenAI, Anthropic, etc.)"""
        return {
            "provider": "openai",  # or "anthropic", "together", etc.
            "model": "gpt-4-turbo",
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "inference": {
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl": 3600,  # 1 hour
                "retry_attempts": 3,
                "retry_backoff": 1.5,
                "timeout": 30
            }
        }

    def _local_config(self) -> Dict[str, Any]:
        """Local CPU configuration"""
        return {
            "model": {
                "name": "phi-2",  # Lighter model for CPU
                "quantization": "q8_0",
                "gpu_memory": 0,
                "num_gpu": 0
            },
            "inference": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 256,
                "num_threads": 8,
                "batch_size": 1
            },
            "performance": {
                "enable_gpu": False,
                "enable_batching": False,
                "enable_kv_cache": True,
                "max_queue_size": 10,
                "request_timeout": 60
            }
        }

    def get_ollama_params(self) -> Dict[str, Any]:
        """Get Ollama API parameters"""
        return {
            "model": self.config["model"]["name"],
            "stream": False,
            "options": {
                "temperature": self.config["inference"]["temperature"],
                "top_p": self.config["inference"]["top_p"],
                "top_k": self.config["inference"]["top_k"],
                "repeat_penalty": self.config["inference"]["repeat_penalty"],
                "num_ctx": self.config["inference"]["num_ctx"],
                "num_predict": self.config["inference"]["num_predict"],
                "num_threads": self.config["inference"]["num_threads"],
            }
        }

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance optimization config"""
        return self.config["performance"]

    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.config["model"]

    def print_config(self):
        """Print configuration for debugging"""
        import json
        log.info(f"\n{'='*60}")
        log.info(f"LLM Configuration ({self.deployment_env})")
        log.info(f"{'='*60}")
        log.info(json.dumps(self.config, indent=2, default=str))
        log.info(f"{'='*60}\n")


class LLMCache:
    """Simple caching layer for LLM responses"""
    def __init__(self, max_cache_size: int = 1000):
        self.cache: Dict[str, str] = {}
        self.max_cache_size = max_cache_size
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[str]:
        """Get cached response"""
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        self.miss_count += 1
        return None

    def set(self, key: str, value: str):
        """Cache response"""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest item
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        self.cache[key] = value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_size": len(self.cache),
            "max_size": self.max_cache_size
        }

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0


class LLMBatcher:
    """Batch multiple requests for efficiency"""
    def __init__(self, batch_size: int = 32, wait_time: float = 0.1):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.pending_requests = []
        self.processed = 0

    def add_request(self, request_id: str, content: str) -> bool:
        """Add request to batch"""
        self.pending_requests.append({
            "id": request_id,
            "content": content
        })
        return len(self.pending_requests) >= self.batch_size

    def get_batch(self) -> Optional[list]:
        """Get ready batch"""
        if len(self.pending_requests) >= self.batch_size:
            batch = self.pending_requests[:self.batch_size]
            self.pending_requests = self.pending_requests[self.batch_size:]
            self.processed += len(batch)
            return batch
        return None

    def get_pending_count(self) -> int:
        """Get count of pending requests"""
        return len(self.pending_requests)

    def get_stats(self) -> Dict[str, Any]:
        """Get batch statistics"""
        return {
            "processed": self.processed,
            "pending": len(self.pending_requests),
            "batch_size": self.batch_size,
            "efficiency": f"{(self.processed / max(1, self.processed + len(self.pending_requests)) * 100):.1f}%"
        }


class PerformanceMonitor:
    """Monitor LLM performance metrics"""
    def __init__(self):
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.error_count = 0
        self.start_time = None

    def record_request(self, tokens: int, latency: float, success: bool = True):
        """Record a request"""
        self.total_requests += 1
        if success:
            self.total_tokens += tokens
            self.total_latency += latency
        else:
            self.error_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_latency = (self.total_latency / max(1, self.total_requests - self.error_count)) if self.total_requests > 0 else 0
        throughput = (self.total_tokens / max(1, self.total_latency)) if self.total_latency > 0 else 0

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.total_requests - self.error_count,
            "failed_requests": self.error_count,
            "error_rate": f"{(self.error_count / max(1, self.total_requests) * 100):.2f}%",
            "avg_latency_ms": f"{avg_latency * 1000:.2f}",
            "tokens_per_second": f"{throughput:.2f}",
            "total_tokens": self.total_tokens
        }

    def reset(self):
        """Reset statistics"""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        self.error_count = 0
