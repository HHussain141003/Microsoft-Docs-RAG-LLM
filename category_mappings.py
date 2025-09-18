CATEGORY_GROUPS = {
    # Power Platform
    'power_platform': [
        'powerapps-overview', 'power-fx', 'maker', 'connect-data', 'transform-model',
        'create-reports', 'collaborate-share', 'alm', 'developer', 'guidance',
        'copilot', 'flow-types', 'regions-overview', 'get-started-logic-flow',
        'run-scheduled-tasks', 'desktop-flows', 'process-mining-overview',
        'introduction', 'release-updates', 'capabilities'
    ],
    
    # Power BI
    'power_bi': [
        'power-bi-overview', 'service-admin-purchasing-power-bi-pro', 'create-reports',
        'collaborate-share', 'consumer', 'desktop', 'paginated-reports-report-builder-power-bi',
        'service-self-service-signup-for-power-bi', 'service-admin-power-bi-security',
        'power-bi-embedded', 'service-collaborate-power-bi-workspace', 'trigger-flow-powerbi-report',
        'service-admin-administering-power-bi-in-your-organization', 'report-server',
        'paginated-reports', 'service-basic-concepts', 'service-dashboards', 'service-share-dashboards'
    ],
    
    # Power Automate
    'power_automate': [
        'flow-types', 'get-started-logic-flow', 'run-scheduled-tasks', 'desktop-flows',
        'all-assigned-must-approve', 'faqs-action-suggestions-power-automate-desktop',
        'process-mining-overview', 'minit', 'automation-center-overview', 'approvals-app-api',
        'create-instant-flows', 'modern-approvals', 'workflow-processes', 'create-flow-solution'
    ],
    
    # Azure Services
    'azure_core': [
        'azure', 'fundamentals', 'core', 'app-service', 'azure-functions', 'virtual-machines',
        'storage', 'azure-resource-manager', 'automation', 'governance', 'networking',
        'security', 'azure-monitor', 'cost-management-billing', 'azure-portal'
    ],
    
    # Azure Data & Analytics
    'azure_data': [
        'databricks', 'synapse-analytics', 'data-factory', 'cosmos-db', 'sql-database',
        'azure-sql', 'data-explorer', 'data-share', 'data-lake-analytics', 'hdinsight',
        'azure-sql-edge', 'analytics-platform-system', 'big-data-cluster'
    ],
    
    # Azure AI/ML
    'azure_ai': [
        'ai-services', 'machine-learning', 'ai', 'cognitive-services', 'ai-foundry',
        'ai-studio', 'azure-video-indexer', 'bot-service', 'applied-ai-services'
    ],
    
    # Development
    'development': [
        'csharp', 'dotnet', 'aspire', 'orleans', 'fsharp', 'visual-basic', 'python',
        'javascript', 'java', 'go', 'devops', 'azure-devops', 'ide', 'debugger',
        'test', 'deployment', 'version-control'
    ],
    
    # Database & SQL
    'database': [
        'sql-server', 'azure-sql', 'database-engine', 'analysis-services',
        'integration-services', 'reporting-services', 'ssms', 'mysql', 'postgresql',
        'mariadb', 'cosmos-db', 'synapse-analytics', 't-sql', 'relational-databases'
    ],
    
    # Microsoft 365
    'microsoft_365': [
        'teams', 'outlook-calendar-concept-overview', 'outlook-mail-concept-overview',
        'sharepoint-concept-overview', 'onedrive-concept-overview', 'excel-concept-overview',
        'teams-concept-overview', 'planner-concept-overview'
    ],
    
    # Security & Compliance
    'security_compliance': [
        'security', 'compliance', 'active-directory', 'sentinel', 'defender-for-cloud',
        'information-protection', 'key-vault', 'security-center', 'gdpr-dsr-summary',
        'privacy-dsr-summary'
    ]
}

QUERY_KEYWORDS = {
    # Power Platform specific
    'powerfx': 'power_platform',
    'power fx': 'power_platform',
    'power platform': 'power_platform',
    'powerapps': 'power_platform',
    'power apps': 'power_platform',
    'canvas app': 'power_platform',
    'model driven': 'power_platform',
    'dataverse': 'power_platform',
    
    # Functions
    'randbetween': 'power_platform',
    'rand': 'power_platform',
    'vlookup': 'power_platform',
    'if function': 'power_platform',
    'sum function': 'power_platform',
    'countif': 'power_platform',
    'concatenate': 'power_platform',
    
    # Power Automate
    'power automate': 'power_automate',
    'flow': 'power_automate',
    'workflow': 'power_automate',
    'approval': 'power_automate',
    'automate': 'power_automate',
    'trigger': 'power_automate',
    'action': 'power_automate',
    'connector': 'power_automate',
    'desktop flow': 'power_automate',
    'process mining': 'power_automate',
    'rpa': 'power_automate',
    
    # Power BI
    'power bi': 'power_bi',
    'powerbi': 'power_bi',
    'dashboard': 'power_bi',
    'report': 'power_bi',
    'visualization': 'power_bi',
    'dataset': 'power_bi',
    'dax': 'power_bi',
    'pbix': 'power_bi',
    
    # Azure Data
    'azure data factory': 'azure_data',
    'data factory': 'azure_data',
    'adf': 'azure_data',
    'pipeline': 'azure_data',
    'databricks': 'azure_data',
    'synapse': 'azure_data',
    'cosmos db': 'azure_data',
    'sql database': 'database',
    'azure sql': 'database',
    
    # Azure AI
    'azure ai': 'azure_ai',
    'cognitive services': 'azure_ai',
    'machine learning': 'azure_ai',
    'bot framework': 'azure_ai',
    'luis': 'azure_ai',
    'qna maker': 'azure_ai',
    
    # Azure Core
    'azure functions': 'azure_core',
    'app service': 'azure_core',
    'virtual machine': 'azure_core',
    'storage account': 'azure_core',
    'resource group': 'azure_core',
    'subscription': 'azure_core',
    
    # Microsoft 365
    'teams': 'microsoft_365',
    'sharepoint': 'microsoft_365',
    'onedrive': 'microsoft_365',
    'outlook': 'microsoft_365',
    'excel': 'microsoft_365',
    'word': 'microsoft_365',
    'powerpoint': 'microsoft_365',
    
    # Development
    'c#': 'development',
    'csharp': 'development',
    '.net': 'development',
    'dotnet': 'development',
    'visual studio': 'development',
    'azure devops': 'development',
    'git': 'development',
    'python': 'development',
    'javascript': 'development',
    
    # Security
    'azure ad': 'security_compliance',
    'active directory': 'security_compliance',
    'authentication': 'security_compliance',
    'authorization': 'security_compliance',
    'compliance': 'security_compliance',
    'gdpr': 'security_compliance',
    'security': 'security_compliance'
}

def get_categories_for_query(query):
    """
    Get relevant category groups for a given query.
    Returns list of categories that might contain relevant documents.
    """
    query_lower = query.lower()
    relevant_groups = set()
    
    for keyword, group in QUERY_KEYWORDS.items():
        if keyword in query_lower:
            relevant_groups.add(group)
    
    categories = []
    for group in relevant_groups:
        if group in CATEGORY_GROUPS:
            categories.extend(CATEGORY_GROUPS[group])
    
    return list(set(categories))

def get_all_categories():
    """Get all available categories."""
    all_cats = []
    for categories in CATEGORY_GROUPS.values():
        all_cats.extend(categories)
    return list(set(all_cats))
