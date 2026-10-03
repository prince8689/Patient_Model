import subprocess
import os

env = os.environ.copy()
env['DIATWIN_DEMO_BUNDLE'] = '1'
env['PYTHONPATH'] = 'd:/Patient_Model'
cwd = 'd:/Patient_Model'

subprocess.run(['python', '-m', 'venv', 'demo_env'], cwd=cwd)
pip = os.path.join(cwd, 'demo_env', 'Scripts', 'pip')
python = os.path.join(cwd, 'demo_env', 'Scripts', 'python')

subprocess.run([pip, 'install', '-r', 'requirements-demo.txt'], cwd=cwd)

while True:
    res = subprocess.run([python, 'scripts/demo_preflight.py'], cwd=cwd, env=env, capture_output=True, text=True)
    if res.returncode != 0 and 'ModuleNotFoundError' in res.stderr:
        missing = res.stderr.split("No module named '")[1].split("'")[0]
        print(f'Missing module: {missing}')
        if missing == 'plotly':
            missing = 'plotly'
        
        with open(os.path.join(cwd, 'requirements-demo.txt'), 'a') as f: 
            f.write(f'{missing}\n')
        subprocess.run([pip, 'install', missing], cwd=cwd)
    else:
        print(res.stdout)
        print(res.stderr)
        break

print('--- requirements-demo.txt ---')
with open(os.path.join(cwd, 'requirements-demo.txt'), 'r', encoding='utf-8') as f:
    print(f.read())
