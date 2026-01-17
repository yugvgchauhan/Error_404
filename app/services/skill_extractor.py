"""Universal NLP-based skill extraction service."""
import re
import json
import os
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher
from collections import defaultdict

# Import PDF/DOCX readers
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class SkillExtractor:
    """Extract skills from any text using comprehensive pattern matching."""
    
    # Comprehensive skill database - covers most technical and soft skills
    TECHNICAL_SKILLS = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby', 'go', 'golang',
        'rust', 'swift', 'kotlin', 'scala', 'php', 'perl', 'r', 'matlab', 'julia', 'dart',
        'objective-c', 'groovy', 'lua', 'haskell', 'erlang', 'elixir', 'clojure', 'f#',
        'assembly', 'cobol', 'fortran', 'vba', 'visual basic', 'shell', 'bash', 'powershell',
        
        # Web Technologies
        'html', 'html5', 'css', 'css3', 'sass', 'scss', 'less', 'tailwind', 'tailwindcss',
        'bootstrap', 'jquery', 'ajax', 'json', 'xml', 'rest', 'restful', 'graphql', 'soap',
        'websocket', 'webrtc', 'pwa', 'spa', 'ssr', 'ssg',
        
        # Frontend Frameworks
        'react', 'reactjs', 'react.js', 'angular', 'angularjs', 'vue', 'vuejs', 'vue.js',
        'svelte', 'next.js', 'nextjs', 'nuxt', 'nuxtjs', 'gatsby', 'ember', 'backbone',
        'redux', 'mobx', 'vuex', 'pinia', 'zustand', 'recoil',
        
        # Backend Frameworks
        'node', 'nodejs', 'node.js', 'express', 'expressjs', 'fastify', 'nest', 'nestjs',
        'django', 'flask', 'fastapi', 'tornado', 'pyramid', 'bottle', 'spring', 'spring boot',
        'springboot', 'hibernate', 'struts', 'rails', 'ruby on rails', 'sinatra', 'laravel',
        'symfony', 'codeigniter', 'asp.net', '.net', '.net core', 'dotnet', 'gin', 'echo',
        'fiber', 'actix', 'rocket',
        
        # Databases
        'sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'oracle', 'sql server', 'mssql',
        'mariadb', 'mongodb', 'mongo', 'cassandra', 'couchdb', 'couchbase', 'redis', 'memcached',
        'elasticsearch', 'opensearch', 'solr', 'neo4j', 'dynamodb', 'firestore', 'firebase',
        'supabase', 'planetscale', 'cockroachdb', 'timescaledb', 'influxdb', 'clickhouse',
        'snowflake', 'bigquery', 'redshift', 'athena', 'presto', 'trino', 'hive', 'hbase',
        'chromadb', 'pinecone', 'weaviate', 'milvus', 'qdrant', 'faiss',
        
        # Cloud Platforms
        'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp', 'google cloud',
        'google cloud platform', 'heroku', 'digitalocean', 'linode', 'vultr', 'cloudflare',
        'vercel', 'netlify', 'render', 'railway', 'fly.io', 'oracle cloud', 'ibm cloud',
        'alibaba cloud', 'tencent cloud',
        
        # AWS Services
        'ec2', 's3', 'lambda', 'rds', 'dynamodb', 'sqs', 'sns', 'cloudwatch', 'cloudfront',
        'route53', 'iam', 'vpc', 'ecs', 'eks', 'fargate', 'elastic beanstalk', 'sagemaker',
        'kinesis', 'emr', 'glue', 'step functions', 'api gateway', 'cognito', 'amplify',
        
        # Azure Services
        'azure functions', 'azure devops', 'azure storage', 'cosmos db', 'azure ml',
        'azure cognitive services', 'azure kubernetes', 'aks', 'azure databricks',
        
        # GCP Services
        'cloud functions', 'cloud run', 'cloud storage', 'bigtable', 'pubsub', 'dataflow',
        'dataproc', 'vertex ai', 'automl', 'cloud composer', 'gke',
        
        # DevOps & Infrastructure
        'docker', 'kubernetes', 'k8s', 'openshift', 'rancher', 'helm', 'istio', 'linkerd',
        'terraform', 'pulumi', 'cloudformation', 'ansible', 'puppet', 'chef', 'saltstack',
        'vagrant', 'packer', 'consul', 'vault', 'nomad',
        
        # CI/CD
        'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis ci', 'teamcity',
        'bamboo', 'azure pipelines', 'argo cd', 'argocd', 'flux', 'spinnaker', 'tekton',
        
        # Version Control
        'git', 'github', 'gitlab', 'bitbucket', 'svn', 'subversion', 'mercurial',
        
        # Testing
        'junit', 'pytest', 'unittest', 'mocha', 'jest', 'jasmine', 'karma', 'cypress',
        'selenium', 'playwright', 'puppeteer', 'testng', 'rspec', 'minitest', 'phpunit',
        'xunit', 'nunit', 'testing library', 'enzyme', 'vitest', 'robot framework',
        
        # Data Science & ML
        'machine learning', 'ml', 'deep learning', 'dl', 'artificial intelligence', 'ai',
        'neural networks', 'natural language processing', 'nlp', 'computer vision', 'cv',
        'reinforcement learning', 'rl', 'supervised learning', 'unsupervised learning',
        'generative ai', 'gen ai', 'llm', 'large language models', 'transformers',
        'gpt', 'bert', 'llama', 'rag', 'retrieval augmented generation', 'fine-tuning',
        'prompt engineering', 'langchain', 'llamaindex', 'huggingface', 'hugging face',
        
        # ML Frameworks
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost', 'lightgbm',
        'catboost', 'prophet', 'statsmodels', 'mlflow', 'kubeflow', 'dvc', 'weights & biases',
        'wandb', 'optuna', 'ray', 'dask', 'spark mllib', 'h2o', 'auto-sklearn', 'autokeras',
        'fastai', 'jax', 'mxnet', 'caffe', 'onnx', 'tensorrt', 'triton',
        
        # Data Processing
        'pandas', 'numpy', 'scipy', 'polars', 'vaex', 'modin', 'cudf', 'dask', 'pyspark',
        'spark', 'apache spark', 'hadoop', 'mapreduce', 'flink', 'kafka', 'apache kafka',
        'airflow', 'apache airflow', 'luigi', 'prefect', 'dagster', 'nifi', 'beam',
        
        # Visualization
        'matplotlib', 'seaborn', 'plotly', 'bokeh', 'd3', 'd3.js', 'chartjs', 'chart.js',
        'highcharts', 'echarts', 'tableau', 'power bi', 'looker', 'metabase', 'superset',
        'grafana', 'kibana', 'streamlit', 'gradio', 'dash', 'panel', 'voila',
        
        # NLP Libraries
        'nltk', 'spacy', 'gensim', 'textblob', 'flair', 'stanza', 'corenlp', 'fasttext',
        'word2vec', 'glove', 'elmo', 'sentence transformers', 'openai', 'anthropic',
        
        # Computer Vision
        'opencv', 'cv2', 'pillow', 'pil', 'imageio', 'skimage', 'scikit-image', 'detectron',
        'yolo', 'yolov5', 'yolov8', 'mmdetection', 'albumentations', 'imgaug',
        
        # Big Data
        'big data', 'data engineering', 'data pipeline', 'etl', 'elt', 'data warehouse',
        'data lake', 'data lakehouse', 'delta lake', 'iceberg', 'hudi', 'dbt',
        
        # APIs & Integration
        'api', 'rest api', 'api development', 'api design', 'swagger', 'openapi', 'postman',
        'insomnia', 'curl', 'grpc', 'protobuf', 'thrift', 'avro', 'webhooks', 'oauth',
        'oauth2', 'jwt', 'saml', 'sso', 'ldap', 'active directory',
        
        # Message Queues
        'rabbitmq', 'activemq', 'zeromq', 'kafka', 'redis', 'celery', 'rq', 'bull',
        'sidekiq', 'aws sqs', 'azure service bus', 'google pubsub',
        
        # Monitoring & Logging
        'prometheus', 'grafana', 'datadog', 'new relic', 'splunk', 'elk', 'elastic stack',
        'logstash', 'fluentd', 'fluent bit', 'jaeger', 'zipkin', 'opentelemetry', 'sentry',
        'pagerduty', 'opsgenie', 'nagios', 'zabbix', 'cloudwatch', 'stackdriver',
        
        # Security
        'security', 'cybersecurity', 'penetration testing', 'pen testing', 'ethical hacking',
        'vulnerability assessment', 'owasp', 'encryption', 'ssl', 'tls', 'https', 'firewall',
        'waf', 'ids', 'ips', 'siem', 'soar', 'devsecops', 'secrets management',
        
        # Mobile Development
        'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova',
        'phonegap', 'swift', 'swiftui', 'kotlin', 'android studio', 'xcode', 'expo',
        
        # Game Development
        'unity', 'unreal engine', 'unreal', 'godot', 'pygame', 'phaser', 'cocos2d',
        'game development', 'gamedev', '3d modeling', 'blender',
        
        # Desktop Development
        'electron', 'tauri', 'qt', 'pyqt', 'tkinter', 'wxpython', 'gtk', 'wpf', 'winforms',
        
        # Embedded & IoT
        'embedded', 'embedded systems', 'iot', 'internet of things', 'arduino', 'raspberry pi',
        'esp32', 'esp8266', 'stm32', 'rtos', 'freertos', 'micropython', 'circuitpython',
        
        # Blockchain
        'blockchain', 'solidity', 'ethereum', 'smart contracts', 'web3', 'web3.js', 'ethers.js',
        'hardhat', 'truffle', 'ganache', 'metamask', 'defi', 'nft',
        
        # Low-Code/No-Code
        'low-code', 'no-code', 'zapier', 'make', 'integromat', 'airtable', 'notion',
        'retool', 'appsmith', 'bubble', 'webflow', 'wordpress',
        
        # Methodologies
        'agile', 'scrum', 'kanban', 'lean', 'waterfall', 'devops', 'devsecops', 'mlops',
        'dataops', 'gitops', 'ci/cd', 'tdd', 'bdd', 'ddd', 'microservices', 'monolith',
        'serverless', 'event-driven', 'cqrs', 'event sourcing',
        
        # Architecture
        'system design', 'software architecture', 'solution architecture', 'enterprise architecture',
        'design patterns', 'solid', 'dry', 'kiss', 'yagni', 'clean code', 'clean architecture',
        'hexagonal architecture', 'onion architecture', 'mvc', 'mvvm', 'mvp',
        
        # Operating Systems
        'linux', 'unix', 'ubuntu', 'debian', 'centos', 'rhel', 'fedora', 'arch linux',
        'windows', 'macos', 'windows server',
        
        # Networking
        'networking', 'tcp/ip', 'tcp', 'udp', 'http', 'https', 'dns', 'dhcp', 'vpn',
        'load balancing', 'nginx', 'apache', 'haproxy', 'traefik', 'caddy', 'envoy',
        
        # Office & Productivity Tools
        'excel', 'microsoft excel', 'google sheets', 'powerpoint', 'word', 'google docs',
        'jira', 'confluence', 'trello', 'asana', 'monday.com', 'notion', 'slack',
        'microsoft teams', 'zoom', 'figma', 'sketch', 'adobe xd', 'invision',
        
        # Healthcare Specific
        'hl7', 'fhir', 'dicom', 'icd-10', 'snomed', 'epic', 'cerner', 'meditech',
        'healthcare analytics', 'clinical data', 'ehr', 'emr', 'hipaa', 'phi',
        'medical imaging', 'radiology', 'pathology', 'genomics', 'bioinformatics',
        
        # Finance Specific  
        'financial modeling', 'quantitative analysis', 'risk management', 'trading',
        'algorithmic trading', 'fintech', 'payment systems', 'banking', 'insurance',
        
        # GIS & Mapping
        'gis', 'arcgis', 'qgis', 'geospatial', 'mapping', 'cartography', 'gdal', 'ogr',
        'leaflet', 'mapbox', 'google maps', 'openstreetmap', 'postgis', 'geopandas',
        'satellite imagery', 'remote sensing', 'ndvi',
        
        # Data Analysis
        'data analysis', 'data analytics', 'business intelligence', 'bi', 'reporting',
        'dashboards', 'kpis', 'metrics', 'statistics', 'statistical analysis',
        'predictive analytics', 'prescriptive analytics', 'descriptive analytics',
        'a/b testing', 'hypothesis testing', 'regression', 'classification', 'clustering',
        
        # Other Technical
        'regex', 'regular expressions', 'latex', 'markdown', 'yaml', 'toml', 'ini',
        'cron', 'scheduling', 'automation', 'scripting', 'web scraping', 'beautifulsoup',
        'scrapy', 'selenium', 'puppeteer', 'playwright',
    }
    
    SOFT_SKILLS = {
        # Leadership & Management
        'leadership', 'team leadership', 'people management', 'mentoring', 'coaching',
        'team building', 'delegation', 'conflict resolution', 'decision making',
        'strategic thinking', 'strategic planning', 'project management', 'program management',
        'product management', 'stakeholder management', 'change management', 'risk management',
        
        # Communication
        'communication', 'verbal communication', 'written communication', 'presentation',
        'public speaking', 'storytelling', 'active listening', 'negotiation', 'persuasion',
        'interpersonal skills', 'cross-functional collaboration', 'client communication',
        'technical writing', 'documentation', 'reporting',
        
        # Problem Solving
        'problem solving', 'critical thinking', 'analytical thinking', 'logical thinking',
        'troubleshooting', 'debugging', 'root cause analysis', 'creative thinking',
        'innovation', 'research', 'data-driven decision making',
        
        # Work Ethics
        'attention to detail', 'time management', 'organizational skills', 'multitasking',
        'prioritization', 'deadline management', 'self-motivated', 'self-starter',
        'initiative', 'proactive', 'accountability', 'reliability', 'dependability',
        'work ethic', 'professionalism', 'integrity', 'ethics',
        
        # Collaboration
        'teamwork', 'collaboration', 'team player', 'cross-team collaboration',
        'remote collaboration', 'distributed teams', 'pair programming', 'code review',
        'knowledge sharing', 'peer feedback',
        
        # Adaptability
        'adaptability', 'flexibility', 'learning agility', 'continuous learning',
        'growth mindset', 'resilience', 'stress management', 'working under pressure',
        'fast-paced environment', 'ambiguity tolerance',
        
        # Customer Focus
        'customer service', 'customer focus', 'user empathy', 'client relations',
        'customer success', 'user experience', 'ux thinking', 'design thinking',
    }
    
    # Skill variations/synonyms mapping
    SKILL_SYNONYMS = {
        'javascript': ['js', 'ecmascript', 'es6', 'es2015', 'es2016', 'es2017', 'es2018', 'es2019', 'es2020', 'es2021', 'es2022'],
        'typescript': ['ts'],
        'python': ['py', 'python3', 'python2'],
        'kubernetes': ['k8s', 'kube'],
        'postgresql': ['postgres', 'psql', 'pgsql'],
        'mongodb': ['mongo'],
        'elasticsearch': ['elastic', 'es'],
        'amazon web services': ['aws'],
        'google cloud platform': ['gcp', 'google cloud'],
        'microsoft azure': ['azure'],
        'machine learning': ['ml'],
        'deep learning': ['dl'],
        'artificial intelligence': ['ai'],
        'natural language processing': ['nlp'],
        'computer vision': ['cv'],
        'continuous integration': ['ci'],
        'continuous deployment': ['cd'],
        'ci/cd': ['cicd', 'ci cd', 'ci-cd'],
        'react': ['reactjs', 'react.js'],
        'vue': ['vuejs', 'vue.js'],
        'angular': ['angularjs', 'angular.js'],
        'node': ['nodejs', 'node.js'],
        'express': ['expressjs', 'express.js'],
        'next.js': ['nextjs', 'next'],
        'scikit-learn': ['sklearn', 'scikit learn'],
        'tensorflow': ['tf'],
        'pytorch': ['torch'],
        '.net': ['dotnet', 'dot net'],
        'c++': ['cpp', 'cplusplus', 'c plus plus'],
        'c#': ['csharp', 'c sharp'],
        'objective-c': ['objc', 'objective c'],
        'visual basic': ['vb', 'vb.net', 'vbnet'],
        'large language models': ['llm', 'llms'],
        'retrieval augmented generation': ['rag'],
        'application programming interface': ['api', 'apis'],
        'user interface': ['ui'],
        'user experience': ['ux'],
        'ui/ux': ['ui ux', 'uiux'],
    }
    
    def __init__(self, skills_file_path: str = None):
        """Initialize with optional custom skills taxonomy."""
        # Build comprehensive skill set
        self.skills_list = self.TECHNICAL_SKILLS | self.SOFT_SKILLS
        
        # Load additional skills from file if provided
        if skills_file_path and os.path.exists(skills_file_path):
            try:
                with open(skills_file_path, 'r', encoding='utf-8') as f:
                    skills_data = json.load(f)
                    # Add custom skills
                    custom_skills = set(s.lower() for s in skills_data.get('skills', []))
                    self.skills_list = self.skills_list | custom_skills
                    
                    # Add custom synonyms
                    custom_synonyms = skills_data.get('synonyms', {})
                    for canonical, variants in custom_synonyms.items():
                        if canonical.lower() not in self.SKILL_SYNONYMS:
                            self.SKILL_SYNONYMS[canonical.lower()] = [v.lower() for v in variants]
            except Exception as e:
                print(f"Warning: Could not load custom skills file: {e}")
        
        # Build reverse synonym map
        self.synonym_map = {}
        for canonical, variants in self.SKILL_SYNONYMS.items():
            for variant in variants:
                self.synonym_map[variant.lower()] = canonical.lower()
        
        # Precompile patterns for multi-word skills
        self._compile_skill_patterns()
    
    def _compile_skill_patterns(self):
        """Compile regex patterns for skill matching."""
        self.skill_patterns = {}
        
        for skill in self.skills_list:
            # Create pattern that matches skill as whole word
            # Handle special regex characters
            escaped = re.escape(skill.lower())
            # Allow for variations like hyphens/spaces/dots
            flexible = escaped.replace(r'\ ', r'[\s\-_.]?')
            flexible = flexible.replace(r'\-', r'[\s\-_.]?')
            flexible = flexible.replace(r'\.', r'[\s\-_.]?')
            
            pattern = rf'\b{flexible}\b'
            try:
                self.skill_patterns[skill] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # Fallback to simple pattern
                self.skill_patterns[skill] = re.compile(rf'\b{re.escape(skill)}\b', re.IGNORECASE)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving important characters."""
        if not text:
            return ""
        
        # Replace common separators with spaces
        text = re.sub(r'[|•·▪►◦‣⁃]', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove extra punctuation but keep important ones
        text = re.sub(r'[^\w\s\-+#./]', ' ', text)
        
        return text.strip()
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from any text using comprehensive pattern matching.
        Works with resumes, job descriptions, or any text.
        """
        if not text:
            return []
        
        found_skills = set()
        text_lower = text.lower()
        text_cleaned = self.clean_text(text_lower)
        
        # 1. Direct pattern matching for all known skills
        for skill, pattern in self.skill_patterns.items():
            if pattern.search(text_cleaned) or pattern.search(text_lower):
                found_skills.add(skill)
        
        # 2. Check synonyms and map to canonical names
        for synonym, canonical in self.synonym_map.items():
            pattern = rf'\b{re.escape(synonym)}\b'
            if re.search(pattern, text_cleaned, re.IGNORECASE):
                found_skills.add(canonical)
        
        # 3. Extract technology patterns (e.g., "Python 3.9", "Java 11")
        version_pattern = r'\b(python|java|php|ruby|node|go|rust|swift|kotlin)\s*[\d.]+\b'
        for match in re.finditer(version_pattern, text_cleaned, re.IGNORECASE):
            found_skills.add(match.group(1).lower())
        
        # 4. Extract framework patterns (e.g., "React 18", "Angular 15")
        framework_pattern = r'\b(react|angular|vue|django|flask|spring|rails|laravel)\s*[\d.]*\b'
        for match in re.finditer(framework_pattern, text_cleaned, re.IGNORECASE):
            found_skills.add(match.group(1).lower())
        
        # 5. Extract cloud service patterns
        cloud_pattern = r'\b(aws|azure|gcp|google\s+cloud)\s+\w+\b'
        for match in re.finditer(cloud_pattern, text_cleaned, re.IGNORECASE):
            # Extract the base cloud platform
            base = match.group(1).lower().replace(' ', '')
            if base == 'googlecloud':
                base = 'gcp'
            found_skills.add(base)
        
        # 6. Extract database patterns
        db_pattern = r'\b(mysql|postgresql|mongodb|redis|elasticsearch|dynamodb|cassandra|sqlite)\s*[\d.]*\b'
        for match in re.finditer(db_pattern, text_cleaned, re.IGNORECASE):
            found_skills.add(match.group(1).lower())
        
        # 7. Look for skills in parentheses (common in resumes)
        # e.g., "Python (NumPy, Pandas, TensorFlow)"
        paren_pattern = r'\(([^)]+)\)'
        for match in re.finditer(paren_pattern, text):
            inner = match.group(1)
            # Split by comma and check each item
            for item in re.split(r'[,;/]', inner):
                item = item.strip().lower()
                if item in self.skills_list:
                    found_skills.add(item)
                elif item in self.synonym_map:
                    found_skills.add(self.synonym_map[item])
        
        # 8. Extract skills from common resume patterns
        # "Skills: Python, Java, SQL" or "Technologies: React, Node"
        skill_section_pattern = r'(?:skills?|technologies?|tools?|languages?|frameworks?|platforms?)\s*[:\-]?\s*([^\n]+)'
        for match in re.finditer(skill_section_pattern, text_lower):
            skill_line = match.group(1)
            for item in re.split(r'[,;|•·]', skill_line):
                item = item.strip().lower()
                # Remove common noise
                item = re.sub(r'\([^)]*\)', '', item).strip()
                if item and len(item) > 1 and len(item) < 50:
                    if item in self.skills_list:
                        found_skills.add(item)
                    elif item in self.synonym_map:
                        found_skills.add(self.synonym_map[item])
                    # Check if it's a multi-word skill
                    for skill in self.skills_list:
                        if skill in item or item in skill:
                            found_skills.add(skill)
                            break
        
        return sorted(list(found_skills))
    
    def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """
        Extract all skills from a resume.
        This is the main method for resume skill extraction.
        """
        if not resume_text:
            return []
        
        # Use the comprehensive text extraction
        skills = self.extract_skills_from_text(resume_text)
        
        # Additional resume-specific extraction
        additional_skills = set()
        
        # Look for bullet point items that might be skills
        bullet_pattern = r'[•·▪►◦‣⁃\-\*]\s*([^\n•·▪►◦‣⁃\-\*]+)'
        for match in re.finditer(bullet_pattern, resume_text):
            bullet_text = match.group(1).strip()
            # Extract skills from each bullet point
            bullet_skills = self.extract_skills_from_text(bullet_text)
            additional_skills.update(bullet_skills)
        
        # Combine all skills
        all_skills = set(skills) | additional_skills
        
        return sorted(list(all_skills))
    
    def extract_skills_with_context(self, text: str) -> Dict[str, Dict]:
        """
        Extract skills with additional context (proficiency indicators, frequency).
        """
        if not text:
            return {}
        
        text_lower = text.lower()
        skills_context = {}
        
        # Get all skills first
        found_skills = self.extract_skills_from_text(text)
        
        # Proficiency indicators
        expert_indicators = ['expert', 'advanced', 'proficient', 'extensive', 'strong', 'deep', 'senior', 'lead', '5+ years', '6+ years', '7+ years', '8+ years', '10+ years']
        intermediate_indicators = ['intermediate', 'good', 'solid', 'working knowledge', '2+ years', '3+ years', '4+ years']
        beginner_indicators = ['beginner', 'basic', 'familiar', 'exposure', 'learning', 'junior', '1 year', '< 1 year']
        
        for skill in found_skills:
            # Count occurrences
            skill_pattern = re.compile(rf'\b{re.escape(skill)}\b', re.IGNORECASE)
            count = len(skill_pattern.findall(text_lower))
            
            # Check for proficiency indicators near the skill
            proficiency = 'unknown'
            confidence = 0.5
            
            # Search within 100 characters of skill mention
            for match in skill_pattern.finditer(text_lower):
                start = max(0, match.start() - 100)
                end = min(len(text_lower), match.end() + 100)
                context = text_lower[start:end]
                
                if any(ind in context for ind in expert_indicators):
                    proficiency = 'expert'
                    confidence = 0.85
                    break
                elif any(ind in context for ind in intermediate_indicators):
                    proficiency = 'intermediate'
                    confidence = 0.70
                elif any(ind in context for ind in beginner_indicators):
                    proficiency = 'beginner'
                    confidence = 0.60
            
            # Boost confidence based on mention count
            if count >= 3:
                confidence = min(confidence + 0.1, 0.95)
            elif count >= 2:
                confidence = min(confidence + 0.05, 0.90)
            
            skills_context[skill] = {
                'mentions': count,
                'proficiency': proficiency,
                'confidence': round(confidence, 2)
            }
        
        return skills_context
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize extracted skills into groups."""
        categories = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'cloud': [],
            'devops': [],
            'data_science': [],
            'soft_skills': [],
            'other': []
        }
        
        # Category patterns
        lang_keywords = {'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala', 'php', 'perl', 'r', 'matlab', 'julia'}
        framework_keywords = {'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express', 'node', 'rails', 'laravel', 'next.js', '.net'}
        db_keywords = {'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb', 'cassandra', 'sqlite', 'oracle', 'firebase'}
        cloud_keywords = {'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'cloudflare', 'vercel', 'ec2', 's3', 'lambda'}
        devops_keywords = {'docker', 'kubernetes', 'jenkins', 'terraform', 'ansible', 'git', 'ci/cd', 'github actions', 'gitlab'}
        ds_keywords = {'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn', 'nlp', 'computer vision', 'data analysis', 'statistics'}
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if skill_lower in self.SOFT_SKILLS or skill_lower in ['leadership', 'communication', 'teamwork', 'problem solving']:
                categories['soft_skills'].append(skill)
            elif skill_lower in lang_keywords:
                categories['programming_languages'].append(skill)
            elif skill_lower in framework_keywords or any(kw in skill_lower for kw in framework_keywords):
                categories['frameworks'].append(skill)
            elif skill_lower in db_keywords or any(kw in skill_lower for kw in db_keywords):
                categories['databases'].append(skill)
            elif skill_lower in cloud_keywords or any(kw in skill_lower for kw in cloud_keywords):
                categories['cloud'].append(skill)
            elif skill_lower in devops_keywords or any(kw in skill_lower for kw in devops_keywords):
                categories['devops'].append(skill)
            elif skill_lower in ds_keywords or any(kw in skill_lower for kw in ds_keywords):
                categories['data_science'].append(skill)
            else:
                categories['other'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    # ==================== File Processing Methods ====================
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not PdfReader:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")
        
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if not Document:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text_parts = []
            
            # Extract from paragraphs
            for paragraph in doc.paragraphs:
                text_parts.append(paragraph.text)
            
            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text_parts.append(cell.text)
            
            return "\n".join(text_parts)
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from file (PDF, DOCX, or TXT)."""
        if not os.path.exists(file_path):
            return ""
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            return ""
    
    # ==================== Proficiency Calculation Methods ====================
    
    def calculate_proficiency_from_text(self, skill: str, text: str) -> Tuple[float, float]:
        """
        Calculate skill proficiency from text mentions and context.
        Returns: (proficiency, confidence)
        """
        text_lower = text.lower()
        skill_lower = skill.lower()
        
        # Count mentions (including synonyms)
        mention_count = len(re.findall(rf'\b{re.escape(skill_lower)}\b', text_lower))
        
        # Check synonyms
        if skill_lower in self.SKILL_SYNONYMS:
            for syn in self.SKILL_SYNONYMS[skill_lower]:
                mention_count += len(re.findall(rf'\b{re.escape(syn)}\b', text_lower))
        
        # Base proficiency from mentions
        if mention_count >= 5:
            base_proficiency = 0.75
        elif mention_count >= 3:
            base_proficiency = 0.65
        elif mention_count >= 2:
            base_proficiency = 0.55
        else:
            base_proficiency = 0.50
        
        # Context boost
        expertise_terms = ['expert', 'proficient', 'advanced', 'extensive', 'strong', 'skilled', 'lead', 'senior']
        for term in expertise_terms:
            # Check if term appears near the skill (within 100 chars)
            # Build two patterns: term before skill, and skill before term
            term_escaped = re.escape(term)
            skill_escaped = re.escape(skill_lower)
            pattern1 = rf'\b{term_escaped}\b.{{0,100}}\b{skill_escaped}\b'
            pattern2 = rf'\b{skill_escaped}\b.{{0,100}}\b{term_escaped}\b'
            if re.search(pattern1, text_lower, re.DOTALL) or re.search(pattern2, text_lower, re.DOTALL):
                base_proficiency += 0.10
                break
        
        confidence = min(0.60 + (mention_count * 0.05), 0.85)
        proficiency = min(base_proficiency, 0.90)
        
        return (round(proficiency, 2), round(confidence, 2))
    
    def calculate_proficiency_from_course(self, skill: str, course_data: Dict) -> Tuple[float, float]:
        """
        Calculate skill proficiency from course data.
        Returns: (proficiency, confidence)
        """
        base_proficiency = 0.5  # Base for course completion
        confidence = 0.7
        
        # Grade boost
        grade = str(course_data.get('grade', '')).upper()
        if grade in ['A+', 'A']:
            base_proficiency += 0.15
            confidence += 0.1
        elif grade in ['A-', 'B+']:
            base_proficiency += 0.10
        elif grade in ['B', 'B-']:
            base_proficiency += 0.05
        
        # Platform reputation boost
        platform = str(course_data.get('platform', '')).lower()
        if platform in ['coursera', 'edx', 'mit', 'stanford', 'udacity', 'google', 'microsoft', 'aws']:
            base_proficiency += 0.05
            confidence += 0.05
        
        # Course level boost (check in name/description)
        text = f"{course_data.get('course_name', '')} {course_data.get('description', '')}".lower()
        if 'advanced' in text or 'expert' in text:
            base_proficiency += 0.10
        elif 'intermediate' in text:
            base_proficiency += 0.05
        
        # Cap at 0.70 (courses have theoretical limit)
        proficiency = min(base_proficiency, 0.70)
        confidence = min(confidence, 0.85)
        
        return (round(proficiency, 2), round(confidence, 2))
    
    def calculate_proficiency_from_project(self, skill: str, project_data: Dict) -> Tuple[float, float]:
        """
        Calculate skill proficiency from project data.
        Returns: (proficiency, confidence)
        """
        base_proficiency = 0.60  # Base for hands-on project
        confidence = 0.75
        
        description = str(project_data.get('description', '')).lower()
        
        # Complexity indicators
        complexity_terms = {
            'deployed': 0.15,
            'production': 0.15,
            'scalable': 0.10,
            'large-scale': 0.10,
            'complex': 0.10,
            'advanced': 0.10,
            'optimized': 0.08,
            'improved': 0.08,
            'integrated': 0.05,
            'api': 0.05,
            'real-time': 0.08,
            'machine learning': 0.10,
            'ai': 0.08,
        }
        
        for term, boost in complexity_terms.items():
            if term in description:
                base_proficiency += boost
                confidence += 0.02
        
        # Team role boost
        role = str(project_data.get('role', '')).lower()
        if 'lead' in role or 'architect' in role:
            base_proficiency += 0.10
            confidence += 0.05
        elif 'solo' in role:
            base_proficiency += 0.05
        
        # Links boost (shows completion/quality)
        if project_data.get('github_link'):
            base_proficiency += 0.05
            confidence += 0.03
        if project_data.get('deployed_link'):
            base_proficiency += 0.10
            confidence += 0.05
        
        # Cap at 0.90 (projects can reach high proficiency)
        proficiency = min(base_proficiency, 0.90)
        confidence = min(confidence, 0.92)
        
        return (round(proficiency, 2), round(confidence, 2))
    
    def calculate_proficiency_from_experience(self, skill: str, exp_data: Dict) -> Tuple[float, float]:
        """
        Calculate skill proficiency from work experience data.
        Returns: (proficiency, confidence)
        """
        base_proficiency = 0.65  # Higher base for work experience
        confidence = 0.80
        
        description = str(exp_data.get('description', '')).lower()
        job_title = str(exp_data.get('job_title', '')).lower()
        
        # Seniority boost
        if any(term in job_title for term in ['senior', 'lead', 'principal', 'staff', 'director']):
            base_proficiency += 0.15
            confidence += 0.10
        elif any(term in job_title for term in ['junior', 'intern', 'trainee']):
            base_proficiency -= 0.10
        
        # Employment type
        emp_type = str(exp_data.get('employment_type', '')).lower()
        if emp_type == 'internship':
            base_proficiency -= 0.10
        elif emp_type in ['full-time', 'contract']:
            base_proficiency += 0.05
        
        # Complexity indicators in description
        if any(term in description for term in ['led', 'architected', 'designed', 'implemented', 'built']):
            base_proficiency += 0.10
            confidence += 0.05
        
        # Cap values
        proficiency = min(max(base_proficiency, 0.40), 0.95)
        confidence = min(confidence, 0.95)
        
        return (round(proficiency, 2), round(confidence, 2))
    
    def aggregate_skills(self, skill_sources: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate skills from multiple sources with weighted averaging.
        """
        skill_data = defaultdict(lambda: {
            'proficiencies': [],
            'confidences': [],
            'sources': [],
            'source_types': []
        })
        
        # Collect all data
        for source_data in skill_sources:
            source_type = source_data.get('source', 'unknown')
            source_id = source_data.get('source_id', 0)
            
            for skill, values in source_data.get('skills', {}).items():
                if isinstance(values, tuple):
                    proficiency, confidence = values
                elif isinstance(values, dict):
                    proficiency = values.get('proficiency', 0.5)
                    confidence = values.get('confidence', 0.5)
                else:
                    continue
                
                skill_data[skill]['proficiencies'].append(proficiency)
                skill_data[skill]['confidences'].append(confidence)
                skill_data[skill]['sources'].append(f"{source_type}:{source_id}")
                skill_data[skill]['source_types'].append(source_type)
        
        # Aggregate with weights
        source_weights = {
            'experience': 2.0,
            'project': 1.5,
            'certification': 1.2,
            'course': 1.0,
            'resume': 1.3,
            'unknown': 1.0
        }
        
        aggregated = {}
        for skill, data in skill_data.items():
            proficiencies = data['proficiencies']
            confidences = data['confidences']
            source_types = data['source_types']
            
            total_weight = sum(source_weights.get(st, 1.0) for st in source_types)
            weighted_prof = sum(
                p * source_weights.get(st, 1.0)
                for p, st in zip(proficiencies, source_types)
            ) / total_weight
            
            # Frequency boost
            source_count = len(proficiencies)
            frequency_boost = min(source_count * 0.05, 0.15)
            
            final_proficiency = min(weighted_prof + frequency_boost, 1.0)
            avg_confidence = sum(confidences) / len(confidences)
            count_boost = min(source_count * 0.1, 0.2)
            final_confidence = min(avg_confidence + count_boost, 0.95)
            
            aggregated[skill] = {
                'proficiency': round(final_proficiency, 2),
                'confidence': round(final_confidence, 2),
                'source_count': source_count,
                'sources': data['sources']
            }
        
        return aggregated
