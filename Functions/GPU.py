from datetime import datetime
import sys
import platform
import subprocess
import shutil

class GPU:
    def print_dashboard(self):
        print("GPU dashboard")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not installed. Install with: conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia")

# --- COLOR CONSTANTS (for terminal) ---
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RED = "\033[91m"

# ---------------------------------
# Detect proper Windows version
# ---------------------------------
def get_windows_version():
    if platform.system() != "Windows":
        return platform.system()
    try:
        output = subprocess.check_output(
            ["wmic", "os", "get", "BuildNumber"], 
            universal_newlines=True,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        ).splitlines()
        build = int([line for line in output if line.strip().isdigit()][0])
        return f"Windows 11 (build {build})" if build >= 22000 else f"Windows 10 (build {build})"
    except Exception:
        return "Windows (version detection failed)"

# ---------------------------------
# Pull live GPU stats via nvidia-smi
# ---------------------------------
def get_nvidia_smi_info():
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            universal_newlines=True,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        ).strip()
        name, vram_total, vram_used, gpu_util, temp = [x.strip() for x in output.split(",")]
        return {
            "name": name,
            "vram_total": float(vram_total),
            "vram_used": float(vram_used),
            "gpu_util": float(gpu_util),
            "temperature": float(temp)
        }
    except Exception:
        return None

# ---------------------------------
# Build dashboard as HTML
# ---------------------------------
def _build_dashboard_html():
    """Build a nicely formatted HTML dashboard"""
    
    if not TORCH_AVAILABLE:
        return "<div style='background: #2d2d2d; color: #ff6b6b; padding: 20px; border-radius: 10px; font-family: monospace;'><h3>⚠️ PyTorch Not Installed</h3><p>Please install PyTorch to use this dashboard.</p></div>"
    
    # Collect all data
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_info = get_windows_version()
    python_ver = sys.version.split()[0]
    pytorch_ver = torch.__version__
    cuda_available = torch.cuda.is_available()
    cuda_ver = torch.version.cuda if cuda_available else "Not available"
    
    # GPU info
    if cuda_available:
        dev = torch.cuda.get_device_properties(0)
        gpu_name = dev.name
        vram_total = f"{dev.total_memory / (1024**3):.2f} GB"
        compute_cap = f"{dev.major}.{dev.minor}"
        sm_count = dev.multi_processor_count
        cuda_alloc = f"{torch.cuda.memory_allocated() / (1024**2):.2f} MB"
        cuda_reserved = f"{torch.cuda.memory_reserved() / (1024**2):.2f} MB"
    else:
        gpu_name = "No CUDA GPU detected"
        vram_total = compute_cap = sm_count = cuda_alloc = cuda_reserved = "N/A"
    
    # Live telemetry
    smi = get_nvidia_smi_info()
    if smi:
        vram_used = f"{smi['vram_used']} / {smi['vram_total']} MB"
        gpu_util = f"{smi['gpu_util']}%"
        temp = f"{smi['temperature']}°C"
    else:
        vram_used = gpu_util = temp = "N/A"
    
    # Build HTML
    html = f"""
    <div style='background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%); 
                color: #e0e0e0; 
                padding: 20px; 
                border-radius: 10px; 
                font-family: "Segoe UI", Arial, sans-serif;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                max-width: 800px;'>
        
        <h2 style='color: #00d9ff; margin: 0 0 20px 0; text-align: center; font-size: 24px;'>
            ⚡ GPU SYSTEM DASHBOARD
        </h2>
        
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;'>
            <div style='background: #252525; padding: 12px; border-radius: 8px; border-left: 3px solid #ffd700;'>
                <div style='color: #999; font-size: 12px;'>🕒 TIME</div>
                <div style='font-size: 16px; margin-top: 5px;'>{now}</div>
            </div>
            <div style='background: #252525; padding: 12px; border-radius: 8px; border-left: 3px solid #ffd700;'>
                <div style='color: #999; font-size: 12px;'>💻 OPERATING SYSTEM</div>
                <div style='font-size: 16px; margin-top: 5px;'>{os_info}</div>
            </div>
            <div style='background: #252525; padding: 12px; border-radius: 8px; border-left: 3px solid #ffd700;'>
                <div style='color: #999; font-size: 12px;'>🐍 PYTHON</div>
                <div style='font-size: 16px; margin-top: 5px;'>{python_ver}</div>
            </div>
            <div style='background: #252525; padding: 12px; border-radius: 8px; border-left: 3px solid #ffd700;'>
                <div style='color: #999; font-size: 12px;'>📦 PYTORCH</div>
                <div style='font-size: 16px; margin-top: 5px;'>{pytorch_ver}</div>
            </div>
        </div>
        
        <div style='background: #252525; padding: 12px; border-radius: 8px; margin-bottom: 20px; border-left: 3px solid #00ff88;'>
            <div style='color: #999; font-size: 12px;'>⚡ CUDA VERSION</div>
            <div style='font-size: 16px; margin-top: 5px;'>{cuda_ver}</div>
        </div>
        
        <h3 style='color: #ff6b6b; margin: 20px 0 15px 0; font-size: 18px;'>🎮 GPU INFORMATION</h3>
        
        <div style='background: #252525; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                <div>
                    <span style='color: #999;'>GPU Name:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{gpu_name}</span>
                </div>
                <div>
                    <span style='color: #999;'>VRAM Total:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{vram_total}</span>
                </div>
                <div>
                    <span style='color: #999;'>Compute Capability:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{compute_cap}</span>
                </div>
                <div>
                    <span style='color: #999;'>SM Count:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{sm_count}</span>
                </div>
                <div>
                    <span style='color: #999;'>CUDA Allocated:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{cuda_alloc}</span>
                </div>
                <div>
                    <span style='color: #999;'>CUDA Reserved:</span>
                    <span style='margin-left: 10px; color: #00ff88;'>{cuda_reserved}</span>
                </div>
            </div>
        </div>
        
        <h3 style='color: #4dabf7; margin: 20px 0 15px 0; font-size: 18px;'>📊 LIVE GPU TELEMETRY</h3>
        
        <div style='background: #252525; padding: 15px; border-radius: 8px;'>
            <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;'>
                <div style='text-align: center;'>
                    <div style='color: #999; font-size: 12px; margin-bottom: 8px;'>VRAM USAGE</div>
                    <div style='font-size: 20px; color: #4dabf7; font-weight: bold;'>{vram_used}</div>
                </div>
                <div style='text-align: center;'>
                    <div style='color: #999; font-size: 12px; margin-bottom: 8px;'>GPU UTILIZATION</div>
                    <div style='font-size: 20px; color: #4dabf7; font-weight: bold;'>{gpu_util}</div>
                </div>
                <div style='text-align: center;'>
                    <div style='color: #999; font-size: 12px; margin-bottom: 8px;'>TEMPERATURE</div>
                    <div style='font-size: 20px; color: #4dabf7; font-weight: bold;'>{temp}</div>
                </div>
            </div>
        </div>
        
    </div>
    """
    
    return html

# ---------------------------------
# Build dashboard as plain text
# ---------------------------------
def _build_dashboard_text():
    """Build plain text dashboard for terminal"""
    
    if not TORCH_AVAILABLE:
        return f"{RED}⚠️  PyTorch Not Installed{RESET}\nPlease install PyTorch to use this dashboard.\nRun: conda install pytorch torchvision torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia"
    
    lines = []
    
    lines.append(BOLD + CYAN + "═══════════════════════════════════════════════════════")
    lines.append("                GPU SYSTEM DASHBOARD")
    lines.append("═══════════════════════════════════════════════════════" + RESET)
    
    lines.append(f"{YELLOW}🕒 Time:{RESET} {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append(f"{YELLOW}💻 OS:{RESET} {get_windows_version()}")
    lines.append(f"{YELLOW}🐍 Python:{RESET} {sys.version.split()[0]}")
    lines.append(f"{YELLOW}📦 PyTorch:{RESET} {torch.__version__}")
    
    if torch.cuda.is_available():
        lines.append(f"{YELLOW}⚡ CUDA:{RESET} {torch.version.cuda}")
    else:
        lines.append(f"{YELLOW}⚡ CUDA:{RESET} Not available (CPU mode)")
    
    lines.append("")
    lines.append(BOLD + MAGENTA + "════════════ GPU INFORMATION ════════════" + RESET)

    if torch.cuda.is_available():
        dev = torch.cuda.get_device_properties(0)
        lines.append(f"{GREEN}GPU Name:{RESET} {dev.name}")
        lines.append(f"{GREEN}VRAM Total:{RESET} {dev.total_memory / (1024**3):.2f} GB")
        lines.append(f"{GREEN}Compute Capability:{RESET} {dev.major}.{dev.minor}")
        lines.append(f"{GREEN}SM Count:{RESET} {dev.multi_processor_count}")
        lines.append(f"{GREEN}CUDA Allocated:{RESET} {torch.cuda.memory_allocated() / (1024**2):.2f} MB")
        lines.append(f"{GREEN}CUDA Reserved:{RESET} {torch.cuda.memory_reserved() / (1024**2):.2f} MB")
    else:
        lines.append(f"{RED}No CUDA GPU detected.{RESET}")

    smi = get_nvidia_smi_info()
    lines.append("")
    if smi:
        lines.append(f"{BLUE}📊 Live GPU Telemetry (via nvidia-smi){RESET}")
        lines.append(f"   VRAM Used: {smi['vram_used']} / {smi['vram_total']} MB")
        lines.append(f"   GPU Utilization: {smi['gpu_util']}%")
        lines.append(f"   Temperature: {smi['temperature']}°C")
    else:
        lines.append(f"{YELLOW}Could not read live GPU stats (nvidia-smi unavailable).{RESET}")

    lines.append(CYAN + "═══════════════════════════════════════════════════════" + RESET)
    
    return "\n".join(lines)

# ---------------------------------
# Public function: print the dashboard
# ---------------------------------
def print_dashboard():
    """
    Displays the GPU dashboard.
    Auto-detects environment: Marimo, Jupyter, or Terminal.
    """
    # Check for Marimo
    if 'marimo' in sys.modules:
        import marimo as mo
        return mo.Html(_build_dashboard_html())
    
    # Check for Jupyter/IPython
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            from IPython.display import display, HTML
            display(HTML(_build_dashboard_html()))
            return
    except (ImportError, AttributeError):
        pass
    
    # Terminal - use colored text
    print(_build_dashboard_text())

# Alias for convenience
show = print_dashboard
dashboard = print_dashboard

# ---------------------------------
# Run dashboard if executed directly
# ---------------------------------
if __name__ == "__main__":
    print_dashboard()