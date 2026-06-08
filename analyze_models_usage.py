#!/usr/bin/env python3
"""
Analyze which ORM models from config/models.yaml are actually used in the codebase.
"""
import os
import re
import glob as fglob

MODELS = [
    "AuditLog", "AIWorkflow", "PageBuilder", "GlobalStyle", "FieldPermission",
    "User", "Article", "Category", "CategorySubscription", "Media",
    "MediaFolder", "MediaOptimization", "ArticleRevisionNote", "SystemSettings",
    "AdminSettings", "ArticleContent", "ArticleLike", "FileHash", "Menus",
    "MenuItems", "MenuLocation", "MenuLocationAssignment", "Pages",
    "UploadTask", "UploadChunk", "DownloadTask", "Notification",
    "SearchHistory", "SearchIndex", "CustomField", "ArticleRevision",
    "Plugin", "Theme", "WidgetInstance", "BlockPattern", "CustomPostType",
    "CommentVote", "CommentSubscription", "Comment", "OAuthAccount",
    "ArticleSEO", "ShareStat", "SensitiveWord", "UserSession",
    "LoginAttempt", "TokenBlacklist", "ArticleAnnotation", "Webhook",
    "WebhookDelivery", "Role", "Capability", "RoleCapability", "UserRole",
    "PermissionAuditLog", "DataSource", "CollectedItem", "Intelligence",
    "Briefing", "AlertRule", "AlertEvent", "KnowledgeBase",
    "KnowledgeDocument", "DocumentChunk", "ReportTemplate",
    "GeneratedReport", "WorkflowDefinition", "WorkflowExecution",
    "NodeExecution", "Trigger", "AgentTool", "AgentMemory",
]

# Non-model keywords that could cause false positives
FALSE_POSITIVES = {
    "User": ["UserAgent", "UserAgentMiddleware", "user_id", "user_agent", "username", "user_session", "user_role", "UserRole", "UserSession", "UserCreate", "UserUpdate"],
}

def search_file(filepath, model_name):
    """Search a file for actual Python imports or class references of model_name."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return False
    
    # Skip binary/large files
    if len(content) > 500000:
        return False
    
    # For Python imports: from shared.models.xxx import ModelName
    # For class references: model_name as a standalone word
    # Pattern matches: import ModelName, ModelName(, from shared.models import ModelName, ModelName as Class
    pattern = r'\b' + re.escape(model_name) + r'\b'
    
    # In Python files, look for actual import or usage
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.py', '.pyx']:
        # Check for explicit import
        import_patterns = [
            rf'from\s+shared\.models\b.*\bimport\b.*\b{re.escape(model_name)}\b',
            rf'\bimport\b.*\b{re.escape(model_name)}\b',
        ]
        for ip in import_patterns:
            if re.search(ip, content):
                return True
        
        # Check for class reference usage (not just string mentions)
        # Look for model name used as a class/type
        class_usage = re.findall(pattern, content)
        if class_usage:
            # Filter out false positives
            if model_name in FALSE_POSITIVES:
                # Check context - is it actually used as a class?
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        line_lower = line.lower()
                        # Skip lines that only mention it in table names or comments
                        if re.search(rf'\b{re.escape(model_name.lower())}\b', line_lower):
                            # Check if it's used as an actual class (import, type hint, SQLAlchemy model)
                            if re.search(rf'from\s+shared\.models', line, re.IGNORECASE):
                                return True
                            if re.search(rf'class\s+{re.escape(model_name)}\b', line):
                                return True
                            if re.search(rf':\s*{re.escape(model_name)}\b', line):
                                return True
                            if re.search(rf'->\s*{re.escape(model_name)}\b', line):
                                return True
                            if re.search(rf'session\.query\(\s*{re.escape(model_name)}\b', line):
                                return True
                            if re.search(rf'\b{re.escape(model_name)}\s*\(', line):
                                # Make sure it's not a false positive keyword
                                is_false = False
                                for fp in FALSE_POSITIVES.get(model_name, []):
                                    if fp in line:
                                        is_false = True
                                        break
                                if not is_false:
                                    return True
            else:
                return True
    
    # For TypeScript/TSX files, look for imports
    if ext in ['.ts', '.tsx', '.js', '.jsx']:
        # Check for import from types/schemas
        if re.search(rf'import\s+.*\b{re.escape(model_name)}\b', content):
            return True
        if re.search(rf'\b{re.escape(model_name)}\b', content):
            return True
    
    return False

def get_all_python_files(dirs):
    files = []
    for d in dirs:
        for root, _, filenames in os.walk(d):
            for fn in filenames:
                if fn.endswith('.py') and not fn.startswith('__'):
                    files.append(os.path.join(root, fn))
                elif fn.endswith(('.ts', '.tsx')):
                    files.append(os.path.join(root, fn))
    return files

# Define key areas to check
base = r'C:\Users\athenavi\AppData\Roaming\reasonix\global-workspace\CardedAI'

areas = {
    'services': os.path.join(base, 'shared', 'services'),
    'api_routes': os.path.join(base, 'src', 'api'),
    'frontend': os.path.join(base, 'frontend-astro', 'src', 'components'),
    'frontend_lib': os.path.join(base, 'frontend-astro', 'src', 'lib'),
    'plugins': os.path.join(base, 'plugins'),
    'scripts': os.path.join(base, 'scripts'),
    'sdk': [os.path.join(base, 'sdk', 'python'), os.path.join(base, 'sdk', 'javascript')],
}

results = {}

for model in MODELS:
    locations = {
        'services': [],
        'api_routes': [],
        'frontend': [],
        'plugins': [],
        'scripts': [],
        'sdk': [],
        'models_dir': [],
    }
    
    # 1. Check shared/services/ for imports
    svc_dir = areas['services']
    if os.path.isdir(svc_dir):
        for root, _, files in os.walk(svc_dir):
            for fn in files:
                if fn.endswith('.py'):
                    fp = os.path.join(root, fn)
                    if search_file(fp, model):
                        rel = os.path.relpath(fp, svc_dir)
                        locations['services'].append(rel)
    
    # 2. Check src/api/ for imports
    api_dir = areas['api_routes']
    if os.path.isdir(api_dir):
        for root, _, files in os.walk(api_dir):
            for fn in files:
                if fn.endswith('.py'):
                    fp = os.path.join(root, fn)
                    if search_file(fp, model):
                        rel = os.path.relpath(fp, api_dir)
                        locations['api_routes'].append(rel)
    
    # 3. Check frontend
    fe_dir = areas['frontend']
    if os.path.isdir(fe_dir):
        for root, _, files in os.walk(fe_dir):
            for fn in files:
                if fn.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    fp = os.path.join(root, fn)
                    if search_file(fp, model):
                        rel = os.path.relpath(fp, fe_dir)
                        locations['frontend'].append(rel)
    
    fe_lib_dir = areas['frontend_lib']
    if os.path.isdir(fe_lib_dir):
        for root, _, files in os.walk(fe_lib_dir):
            for fn in files:
                if fn.endswith(('.ts', '.tsx')):
                    fp = os.path.join(root, fn)
                    if search_file(fp, model):
                        rel = os.path.relpath(fp, fe_lib_dir)
                        locations['frontend'].append(os.path.join('lib', rel))
    
    # 4. Check plugins
    pl_dir = areas['plugins']
    if os.path.isdir(pl_dir):
        for root, _, files in os.walk(pl_dir):
            for fn in files:
                if fn.endswith('.py'):
                    fp = os.path.join(root, fn)
                    if search_file(fp, model):
                        rel = os.path.relpath(fp, pl_dir)
                        locations['plugins'].append(rel)
    
    # 5. Check scripts
    sc_dir = areas['scripts']
    if os.path.isdir(sc_dir):
        for fn in os.listdir(sc_dir):
            if fn.endswith('.py'):
                fp = os.path.join(sc_dir, fn)
                if search_file(fp, model):
                    locations['scripts'].append(fn)
    
    # 6. Check shared/models/ itself (the model definition)
    models_dir = os.path.join(base, 'shared', 'models')
    model_file = None
    if os.path.isdir(models_dir):
        for root, _, files in os.walk(models_dir):
            for fn in files:
                if fn.endswith('.py'):
                    fp = os.path.join(root, fn)
                    if model.lower() in fn.lower():
                        if search_file(fp, model):
                            model_file = fp
                            rel = os.path.relpath(fp, models_dir)
                            locations['models_dir'].append(rel)
    
    total_uses = sum(1 for k, v in locations.items() if v)
    results[model] = {
        'total_locations': total_uses,
        'locations': locations,
        'has_service': len(locations['services']) > 0,
        'has_api': len(locations['api_routes']) > 0,
        'has_frontend': len(locations['frontend']) > 0,
    }

# Print results
for model, data in sorted(results.items(), key=lambda x: (x[1]['total_locations'], x[0])):
    svcs = ', '.join(data['locations']['services']) if data['locations']['services'] else '-'
    apis = ', '.join(data['locations']['api_routes'][:3]) if data['locations']['api_routes'] else '-'
    fes = ', '.join(data['locations']['frontend'][:3]) if data['locations']['frontend'] else '-'
    pls = ', '.join(data['locations']['plugins'][:3]) if data['locations']['plugins'] else '-'
    
    status = "[UNUSED]"
    if data['total_locations'] >= 2 and data['has_service'] and (data['has_api'] or data['has_frontend']):
        status = "[ACTIVE]"
    elif data['total_locations'] >= 1:
        status = "[PARTIAL]"
    
    print(f"\n{status}  {model}")
    print(f"     Services: {svcs}")
    print(f"     API: {apis}")
    print(f"     Frontend: {fes}")
    print(f"     Plugins: {pls}")
    print(f"     Total areas: {data['total_locations']}")

print("\n\n=== SUMMARY ===")
active = [m for m, d in results.items() if d['total_locations'] >= 2 and d['has_service'] and (d['has_api'] or d['has_frontend'])]
partial = [m for m, d in results.items() if d['total_locations'] >= 1 and not (d['total_locations'] >= 2 and d['has_service'] and (d['has_api'] or d['has_frontend']))]
unused = [m for m, d in results.items() if d['total_locations'] == 0]

print(f"\n[ACTIVE] ({len(active)}): {', '.join(sorted(active))}")
print(f"\n[PARTIAL] ({len(partial)}): {', '.join(sorted(partial))}")
print(f"\n[UNUSED] ({len(unused)}): {', '.join(sorted(unused))}")
