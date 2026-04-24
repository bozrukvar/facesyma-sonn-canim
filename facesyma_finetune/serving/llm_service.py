#!/usr/bin/env python3
"""Direct GPT2 serving without vLLM (Windows compatible)"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

import os
model_path = os.path.abspath("../training/facesyma-gpt2-lora/checkpoint-12000")

# Load base model
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

print("Loading base model...")
model = AutoModelForCausalLM.from_pretrained("gpt2", torch_dtype=torch.float16, device_map="cuda")

# Load LoRA adapters
print("Loading LoRA adapters...")
model = PeftModel.from_pretrained(model, model_path)
model.eval()

print("✓ Model loaded!\n")

def generate(prompt, max_tokens=128):
    """Generate text from prompt"""
    # Truncate prompt to fit within model's max length
    tokens = tokenizer.encode(prompt, return_tensors="pt")
    max_prompt_length = 512  # Leave room for generation
    if tokens.shape[1] > max_prompt_length:
        tokens = tokens[:, -max_prompt_length:]

    inputs = tokens.to("cuda")
    _teid = tokenizer.eos_token_id
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=max_tokens,  # Only new tokens
            pad_token_id=_teid,
            eos_token_id=_teid,
            attention_mask=torch.ones_like(inputs),
            do_sample=False,  # Greedy
            num_beams=1,
            no_repeat_ngram_size=2  # No repetition
        )

    # Get only generated part (remove input)
    generated = outputs[0][inputs.shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)

if __name__ == "__main__":
    # Test
    result = generate("Merhaba, ben")
    print(f"Output: {result}\n")
