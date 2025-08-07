#!/usr/bin/env python3
"""
Test data for the Candidate Recommendation Engine
Contains sample resumes and job descriptions for testing.
"""

# Sample job descriptions
JOB_DESCRIPTIONS = {
    "software_engineer": """
    Software Engineer - Python Developer
    
    We are looking for a talented Software Engineer with strong Python experience to join our team.
    
    Requirements:
    - 3+ years of experience in Python development
    - Experience with web frameworks (Django, Flask)
    - Knowledge of databases (PostgreSQL, MySQL)
    - Experience with version control (Git)
    - Strong problem-solving skills
    
    Responsibilities:
    - Develop and maintain web applications
    - Write clean, maintainable code
    - Collaborate with cross-functional teams
    - Participate in code reviews
    """,
    
    "data_scientist": """
    Data Scientist
    
    We are seeking a Data Scientist to help us extract insights from large datasets.
    
    Requirements:
    - 2+ years of experience in data science
    - Proficiency in Python, R, or SQL
    - Experience with machine learning algorithms
    - Knowledge of statistical analysis
    - Experience with data visualization tools
    
    Responsibilities:
    - Analyze large datasets
    - Build predictive models
    - Create data visualizations
    - Present findings to stakeholders
    """
}

# Sample resumes
SAMPLE_RESUMES = [
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(123) 456-7890",
        "text": """
        John Doe
        Software Engineer
        john.doe@example.com
        (123) 456-7890
        
        Experience:
        - Senior Software Engineer at TechCorp (2020-2023)
          * Developed Python web applications using Django
          * Led team of 3 developers
          * Improved application performance by 40%
        
        - Software Engineer at StartupXYZ (2018-2020)
          * Built REST APIs using Flask
          * Worked with PostgreSQL and Redis
          * Implemented CI/CD pipelines
        
        Skills:
        - Python, Django, Flask, JavaScript, React
        - PostgreSQL, MySQL, Redis, Git
        - Docker, AWS, Linux
        """
    },
    
    {
        "name": "Jane Smith",
        "email": "jane.smith@example.com", 
        "phone": "(987) 654-3210",
        "text": """
        Jane Smith
        Data Scientist
        jane.smith@example.com
        (987) 654-3210
        
        Experience:
        - Data Scientist at DataCorp (2021-2023)
          * Built machine learning models for customer segmentation
          * Analyzed large datasets using Python and SQL
          * Created data visualizations with Tableau
        
        - Junior Data Analyst at AnalyticsInc (2019-2021)
          * Performed statistical analysis on business data
          * Created reports and dashboards
          * Collaborated with business stakeholders
        
        Skills:
        - Python, R, SQL, Pandas, NumPy, Scikit-learn
        - Tableau, Power BI, Jupyter Notebooks
        - Statistical analysis, Machine Learning
        """
    },
    
    {
        "name": "Bob Wilson",
        "email": "bob.wilson@example.com",
        "phone": "(555) 123-4567", 
        "text": """
        Bob Wilson
        Product Manager
        bob.wilson@example.com
        (555) 123-4567
        
        Experience:
        - Senior Product Manager at ProductCorp (2019-2023)
          * Led product strategy for B2B SaaS platform
          * Managed team of 8 developers and designers
          * Increased user engagement by 60%
        
        - Product Manager at StartupABC (2017-2019)
          * Launched mobile app with 100K+ users
          * Conducted user research and A/B testing
          * Worked closely with engineering team
        
        Skills:
        - Product strategy, User research, A/B testing
        - Agile methodologies, JIRA, Figma
        - Data analysis, SQL, Python basics
        """
    },
    
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "phone": "(444) 555-6666",
        "text": """
        Alice Johnson
        Frontend Developer
        alice.johnson@example.com
        (444) 555-6666
        
        Experience:
        - Frontend Developer at WebCorp (2020-2023)
          * Built responsive web applications using React
          * Implemented modern UI/UX designs
          * Optimized application performance
        
        - Junior Developer at DevStart (2018-2020)
          * Developed websites using HTML, CSS, JavaScript
          * Worked with WordPress and PHP
          * Collaborated with design team
        
        Skills:
        - JavaScript, React, Vue.js, TypeScript
        - HTML5, CSS3, SASS, Bootstrap
        - Webpack, Git, Figma
        """
    }
]

# Duplicate test data
DUPLICATE_TEST_DATA = [
    # Original candidate
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "(123) 456-7890",
        "text": "Software Engineer with 5 years of Python experience"
    },
    # Duplicate email
    {
        "name": "John Smith", 
        "email": "john.doe@example.com",  # Same email
        "phone": "(987) 654-3210",
        "text": "Data Scientist with 3 years experience"
    },
    # Duplicate content
    {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "(555) 123-4567", 
        "text": "Software Engineer with 5 years of Python experience"  # Same content
    },
    # Duplicate name+email
    {
        "name": "John Doe",
        "email": "john.doe@example.com",  # Same name and email
        "phone": "(123) 456-7890",
        "text": "Different content but same person"
    }
]

def get_test_job_description(job_type="software_engineer"):
    """Get a test job description."""
    return JOB_DESCRIPTIONS.get(job_type, JOB_DESCRIPTIONS["software_engineer"])

def get_test_resumes():
    """Get all test resumes."""
    return SAMPLE_RESUMES

def get_duplicate_test_data():
    """Get test data with duplicates."""
    return DUPLICATE_TEST_DATA

def get_single_resume(index=0):
    """Get a single test resume."""
    return SAMPLE_RESUMES[index] if 0 <= index < len(SAMPLE_RESUMES) else SAMPLE_RESUMES[0]
