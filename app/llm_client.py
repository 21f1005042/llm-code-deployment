import os
import json
import logging
from typing import List, Dict, Any, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.model_name = "codellama/CodeLlama-7b-hf"  # You can change this model
        self.tokenizer = None
        self.model = None
        self.generator = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Hugging Face model"""
        try:
            # Use smaller model for demo, adjust based on your needs
            self.model_name = "microsoft/DialoGPT-medium"
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                max_length=1024
            )
            logger.info(f"Initialized model: {self.model_name}")
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            # Fallback to a simpler approach
            self.generator = None
    
    async def generate_app_code(self, brief: str, checks: List[str], 
                              attachments: List[str] = None,
                              existing_repo: str = None) -> Dict[str, str]:
        """Generate application code based on brief and checks"""
        
        prompt = self._build_prompt(brief, checks, attachments, existing_repo)
        
        try:
            if self.generator:
                # Use Hugging Face pipeline
                result = self.generator(
                    prompt,
                    max_new_tokens=1024,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=50256
                )
                generated_text = result[0]['generated_text']
            else:
                # Fallback: return template code
                generated_text = self._generate_template_code(brief, checks)
            
            # Parse generated code
            code_files = self._parse_generated_code(generated_text, brief)
            return code_files
            
        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            return self._generate_fallback_code(brief, checks)
    
    def _build_prompt(self, brief: str, checks: List[str], 
                     attachments: List[str] = None,
                     existing_repo: str = None) -> str:
        """Build prompt for code generation"""
        
        prompt = f"""
        Create a complete web application based on this brief:
        
        BRIEF: {brief}
        
        REQUIREMENTS:
        {chr(10).join(f"- {check}" for check in checks)}
        
        {"EXISTING REPOSITORY: " + existing_repo if existing_repo else "NEW APPLICATION"}
        
        Generate the following files in JSON format:
        {{
            "README.md": "Complete README with setup instructions",
            "index.html": "Main HTML file",
            "style.css": "CSS styles",
            "script.js": "JavaScript functionality",
            "LICENSE": "MIT License content"
        }}
        
        Ensure the code is:
        - Complete and runnable
        - Well-documented
        - Follows best practices
        - Meets all requirements
        
        Return only valid JSON:
        """
        
        return prompt
    
    def _parse_generated_code(self, generated_text: str, brief: str) -> Dict[str, str]:
        """Parse generated text into code files"""
        try:
            # Extract JSON from generated text
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            json_str = generated_text[json_start:json_end]
            
            code_files = json.loads(json_str)
        except:
            # Fallback if JSON parsing fails
            code_files = self._generate_template_code_dict(brief)
        
        # Ensure all required files are present
        required_files = ['README.md', 'index.html', 'style.css', 'script.js', 'LICENSE']
        for file in required_files:
            if file not in code_files:
                code_files[file] = self._get_template_file(file, brief)
        
        return code_files
    
    def _generate_template_code(self, brief: str, checks: List[str]) -> str:
        """Generate template code as fallback"""
        return json.dumps(self._generate_template_code_dict(brief))
    
    def _generate_template_code_dict(self, brief: str) -> Dict[str, str]:
        """Generate template code files"""
        return {
            "README.md": f"# Generated App\n\n{brief}\n\n## Setup\nOpen index.html in a browser.",
            "index.html": self._get_template_file("index.html", brief),
            "style.css": self._get_template_file("style.css", brief),
            "script.js": self._get_template_file("script.js", brief),
            "LICENSE": self._get_template_file("LICENSE", brief)
        }
    
    def _generate_fallback_code(self, brief: str, checks: List[str]) -> Dict[str, str]:
        """Generate fallback code when generation fails"""
        return self._generate_template_code_dict(brief)
    
    def _get_template_file(self, filename: str, brief: str) -> str:
        """Get template content for files"""
        templates = {
            "README.md": f"""# Generated Application

## Description
{brief}

## Setup
1. Clone this repository
2. Open `index.html` in a web browser
3. No build process required

## Features
- Responsive design
- Modern UI components
- Cross-browser compatible

## License
MIT License
""",
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated App</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <h1>Generated Application</h1>
        <div id="app-content">
            <p>Application content will be loaded here.</p>
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>""",
            "style.css": """/* Generated Application Styles */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    text-align: center;
}

#app-content {
    margin-top: 20px;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 4px;
}""",
            "script.js": """// Generated Application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Generated application loaded');
    
    // Basic functionality
    const appContent = document.getElementById('app-content');
    if (appContent) {
        appContent.innerHTML = '<p>Application is running successfully!</p>';
    }
});""",
            "LICENSE": """MIT License

Copyright (c) 2024 Generated Application

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        }
        
        return templates.get(filename, f"# {filename}\n\nContent for {filename}")