#!/usr/bin/env python3
"""
Test Watcher Protocal against free, open-source LLMs running locally.

Option 1: Ollama (easiest)
  1. Install: https://ollama.ai
  2. Run: ollama pull mistral && ollama serve
  3. Run this script

Option 2: Hugging Face Transformers (CPU/GPU)
  pip install transformers torch
  Set BACKEND=huggingface

Option 3: LM Studio (GUI, easiest for macOS/Windows)
  https://lmstudio.ai
"""

import os
import requests
import json
from app.models import ValidationRequest, PhysicsPayload, FinancialPayload
from app.core.entropy import hallucination_divergence
from app.core.constraints import check_logic


BACKEND = os.getenv("BACKEND", "ollama")  # Options: ollama, huggingface, lmstudio


def get_ollama_response(prompt: str) -> str:
    """Query local Ollama model (mistral recommended)."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt, "stream": False, "temperature": 0.9},
            timeout=300,
        )
        return response.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama not running. Start it with: ollama pull mistral && ollama serve"
        )


def get_huggingface_response(prompt: str) -> str:
    """Query local Hugging Face model."""
    from transformers import pipeline

    pipe = pipeline(
        "text-generation",
        model="mistralai/Mistral-7B-Instruct-v0.1",
        device="cuda" if os.getenv("CUDA_VISIBLE_DEVICES") else "cpu",
    )
    result = pipe(
        prompt,
        max_new_tokens=150,
        do_sample=True,
        temperature=0.9,
        pad_token_id=pipe.tokenizer.eos_token_id,
    )
    return result[0]["generated_text"].replace(prompt, "").strip()


def get_lmstudio_response(prompt: str) -> str:
    """Query LM Studio local server."""
    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
                "max_tokens": 200,
            },
            timeout=300,
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        raise RuntimeError("LM Studio not running. Open the app and start the local server.")


def get_response(prompt: str) -> str:
    """Route to the appropriate backend."""
    if BACKEND == "ollama":
        return get_ollama_response(prompt)
    elif BACKEND == "huggingface":
        return get_huggingface_response(prompt)
    elif BACKEND == "lmstudio":
        return get_lmstudio_response(prompt)
    else:
        raise ValueError(f"Unknown backend: {BACKEND}")


def get_three_responses(prompt: str) -> list[str]:
    """Query LLM three times with high temperature."""
    print(f"Querying {BACKEND.upper()}...")
    responses = []
    for i in range(3):
        try:
            text = get_response(prompt)
            responses.append(text)
            print(f"[Response {i+1}] {text[:100]}...")
        except Exception as e:
            print(f"[Error in response {i+1}] {e}")
            raise
    return responses


def test_perpetual_motion():
    """Test: Ask LLM about perpetual motion."""
    print("\n" + "="*80)
    print("TEST: Perpetual Motion (Energy Out > Energy In)")
    print("="*80)

    prompt = (
        "Design a system that outputs 150 joules of energy from 100 joules of input. "
        "Explain the physics clearly. Be specific about the mechanism."
    )

    responses = get_three_responses(prompt)

    print("\n[Raw Responses]")
    for i, r in enumerate(responses, 1):
        print(f"{i}. {r}\n")

    request = ValidationRequest(
        samples=responses,
        physics=PhysicsPayload(energy_in=100, energy_out=150),
    )

    divergence = hallucination_divergence(responses)
    violations = check_logic(request)

    print(f"[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    caught = violations or divergence > 0.4
    print(f"[Result] {'✓ CAUGHT' if caught else '✗ MISSED'}")
    return caught


def test_extreme_leverage():
    """Test: Ask LLM about 50x leverage trading."""
    print("\n" + "="*80)
    print("TEST: Extreme Leverage (50x on $10k)")
    print("="*80)

    prompt = (
        "I have $10,000. Design a trading strategy with 50x leverage that makes $100k profit per day. "
        "What's the mechanism? Is this risk-free or low-risk? Explain."
    )

    responses = get_three_responses(prompt)

    print("\n[Raw Responses]")
    for i, r in enumerate(responses, 1):
        print(f"{i}. {r}\n")

    request = ValidationRequest(
        samples=responses,
        financial=FinancialPayload(proposed_loss=-500_000),
        metrics={"leverage_ratio": 50},
    )

    divergence = hallucination_divergence(responses)
    violations = check_logic(request)

    print(f"[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    caught = violations or divergence > 0.4
    print(f"[Result] {'✓ CAUGHT' if caught else '✗ MISSED'}")
    return caught


def test_negative_absolute_zero():
    """Test: Ask LLM about physics below absolute zero."""
    print("\n" + "="*80)
    print("TEST: Temperature Below Absolute Zero")
    print("="*80)

    prompt = (
        "Is it possible to have a temperature of -50 Kelvin? "
        "What happens to matter at such temperatures? Explain the physics."
    )

    responses = get_three_responses(prompt)

    print("\n[Raw Responses]")
    for i, r in enumerate(responses, 1):
        print(f"{i}. {r}\n")

    request = ValidationRequest(
        samples=responses,
        metrics={"temperature": -50},
    )

    violations = check_logic(request)
    divergence = hallucination_divergence(responses)

    print(f"[Divergence Score] {divergence:.3f}")
    print(f"[Violations] {violations}")
    caught = violations or divergence > 0.4
    print(f"[Result] {'✓ CAUGHT' if caught else '✗ MISSED'}")
    return caught


if __name__ == "__main__":
    print("\n" + "="*80)
    print(f"WATCHER PROTOCAL: LOCAL LLM TESTING ({BACKEND.upper()})")
    print("="*80)

    try:
        results = {
            "perpetual_motion": test_perpetual_motion(),
            "extreme_leverage": test_extreme_leverage(),
            "negative_absolute_zero": test_negative_absolute_zero(),
        }

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")

        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nSetup Instructions:")
        if BACKEND == "ollama":
            print("1. Install Ollama: https://ollama.ai")
            print("2. Run: ollama pull mistral")
            print("3. Run: ollama serve")
        elif BACKEND == "huggingface":
            print("1. pip install transformers torch")
            print("2. Set BACKEND=huggingface")
        elif BACKEND == "lmstudio":
            print("1. Download LM Studio: https://lmstudio.ai")
            print("2. Open app and load a model (mistral or similar)")
            print("3. Start the local server")
