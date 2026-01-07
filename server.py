#!/usr/bin/env python3
import os
import sys
import re
import time
from typing import List

# --- BOOTSTRAP PATHING ---
# Ensure the main directory is in the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, request, redirect

# --- ROBUST IMPORTS ---
# We use a forced package import strategy to avoid conflicts with system modules named 'parser'
try:
    # Most reliable: Import from the ducky package
    from ducky import parser as ducky_parser
    from ducky import exceptions as ducky_exceptions
    
    parse = ducky_parser.parse
    Command = ducky_parser.Command
    DuckyParseError = ducky_exceptions.DuckyParseError
except (ImportError, ModuleNotFoundError):
    try:
        # Fallback: Absolute imports from root
        import parser as ducky_parser
        import exceptions as ducky_exceptions
        
        parse = ducky_parser.parse
        Command = ducky_parser.Command
        DuckyParseError = ducky_exceptions.DuckyParseError
    except ImportError as e:
        # Final Debugging info for the user
        print(f"CRITICAL ERROR: Could not find ducky modules.")
        print(f"Base Dir: {BASE_DIR}")
        print(f"Contents of {BASE_DIR}: {os.listdir(BASE_DIR)}")
        if os.path.exists(os.path.join(BASE_DIR, 'ducky')):
            print(f"Contents of ducky folder: {os.listdir(os.path.join(BASE_DIR, 'ducky'))}")
        print(f"Error Detail: {e}")
        sys.exit(1)

app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='static')

# --- CONFIGURATION ---
HID_DEVICE = os.environ.get('HID_DEVICE', '/dev/hidg0')
SCRIPTS_DIR = os.environ.get('SCRIPTS_DIR', os.path.join(BASE_DIR, 'scripts'))

if not os.path.exists(SCRIPTS_DIR):
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

def list_scripts():
    try:
        return sorted([f for f in os.listdir(SCRIPTS_DIR) 
                if os.path.isfile(os.path.join(SCRIPTS_DIR, f)) and not f.startswith('.')])
    except OSError:
        return []

def write_keystrokes(commands: List[Command]):
    with open(HID_DEVICE, 'wb') as dev:
        for command in commands:
            if command.payload:
                dev.write(command.payload)
                dev.flush()
            if command.delay > 0:
                delay_seconds = command.delay / 1000.0
                time.sleep(delay_seconds)

def validate_script_name(name: str):
    if not name:
        raise ValueError('Filename cannot be empty')
    if not re.match(r'^[\w\.\-\_]+$', name):
        raise ValueError('Names can contain letters, numbers, dots, hyphens, and underscores only.')

@app.route('/', methods=['GET', 'POST'])
def live():
    scripts = list_scripts()
    form_data = request.form.to_dict() if request.method == 'POST' else {}
    
    if request.method == 'GET':
        load = request.args.get('load')
        if load:
            try:
                validate_script_name(load)
                path = os.path.join(SCRIPTS_DIR, load)
                with open(path, 'r') as fd:
                    form_data['script'] = fd.read()
            except Exception as e:
                return render_template('index.html', form=form_data, scripts=scripts, error=str(e))
        
        msg = request.args.get('msg')
        return render_template('index.html', form=form_data, scripts=scripts, msg=msg)

    # POST Handling
    content = form_data.get('script', '')
    action = form_data.get('action')
    
    try:
        commands = parse(content) if content else []
    except DuckyParseError as pe:
        return render_template('index.html', form=form_data, scripts=scripts, error=f"Parse Error: {str(pe)}")

    if action == 'validate':
        return render_template('index.html', form=form_data, scripts=scripts, validated=True)
    
    elif action == 'save':
        try:
            name = form_data.get('name')
            validate_script_name(name)
            if not name.lower().endswith('.ducky'):
                name += '.ducky'
            path = os.path.join(SCRIPTS_DIR, name)
            with open(path, 'w') as fd:
                fd.write(content)
            return redirect('/?msg=saved')
        except Exception as e:
            return render_template('index.html', form=form_data, scripts=scripts, error=str(e))
    
    elif action == 'run':
        try:
            if not commands:
                raise ValueError("The script is empty. Nothing to run.")
            write_keystrokes(commands)
            return render_template('index.html', form=form_data, scripts=scripts, validated=True)
        except Exception as e:
            return render_template('index.html', form=form_data, scripts=scripts, error=str(e))

    return render_template('index.html', form=form_data, scripts=scripts)

@app.route('/delete')
def delete_script():
    name = request.args.get('script')
    try:
        validate_script_name(name)
        path = os.path.join(SCRIPTS_DIR, name)
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        return str(e), 400
    return redirect('/?msg=deleted')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)