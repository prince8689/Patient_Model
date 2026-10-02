import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')

    # Color palette
    colors = {
        'data': '#e2e8f0',
        'features': '#cbd5e1',
        'frozen': '#f87171',
        'engine': '#93c5fd',
        'ui': '#6ee7b7'
    }

    # Draw boxes
    boxes = [
        # x, y, w, h, label, color
        (0.5, 4.5, 2, 1, "EHR Data", colors['data']),
        (0.5, 3.0, 2, 1, "Wearable", colors['data']),
        
        (3.5, 3.75, 2, 1, "Feature Eng", colors['features']),
        
        (6.5, 4.5, 2, 1, "Risk Model", colors['frozen']),
        (6.5, 3.0, 2, 1, "Forecaster", colors['frozen']),
        
        (3.5, 1.5, 5, 1, "Twin State Engine", colors['engine']),
        (3.5, 0.0, 2, 1, "What-if Sim", colors['engine']),
        
        (9.5, 2.25, 2, 2.5, "Dashboard\n(Display Only)", colors['ui'])
    ]

    for x, y, w, h, label, col in boxes:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=col)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=10, weight='bold')

    # Arrows
    arrows = [
        ((2.5, 5.0), (3.5, 4.5)),
        ((2.5, 3.5), (3.5, 4.0)),
        ((5.5, 4.25), (6.5, 4.75)),
        ((5.5, 4.25), (6.5, 3.5)),
        ((4.5, 3.75), (4.5, 2.5)),
        ((7.5, 4.5), (7.5, 2.5)),
        ((7.5, 3.0), (7.5, 2.5)),
        ((4.5, 1.5), (4.5, 1.0)),
        ((8.5, 2.0), (9.5, 3.0))
    ]
    
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5))
        
    # Frozen Boundary
    rect = patches.Rectangle((6.2, 2.7), 2.6, 3.1, linewidth=2, edgecolor=colors['frozen'], facecolor='none', linestyle='--')
    ax.add_patch(rect)
    ax.text(7.5, 6.0, "Frozen Artifacts", ha='center', va='center', color=colors['frozen'], weight='bold')
    
    plt.tight_layout()
    plt.savefig("docs/images/architecture.png", dpi=150, bbox_inches='tight')
    plt.close()

def create_data_flow():
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')
    
    colors = {'storage': '#f1f5f9', 'process': '#bae6fd'}
    
    boxes = [
        (1, 2.5, 2, 1, "Raw Data & \nModels", colors['storage']),
        (4, 2.5, 2, 1, "Insights Builder", colors['process']),
        (7, 2.5, 2, 1, "Demo Bundle \n(JSON)", colors['storage']),
        (4, 0.5, 2, 1, "Hosted App", colors['process']),
        (7, 0.5, 2, 1, "Demo Viewer", colors['storage'])
    ]
    
    for x, y, w, h, label, col in boxes:
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=col)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=10, weight='bold')
        
    arrows = [
        ((3, 3.0), (4, 3.0)),
        ((6, 3.0), (7, 3.0)),
        ((8, 2.5), (8, 1.5)),
        ((6, 1.0), (7, 1.0))
    ]
    
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.5))

    plt.tight_layout()
    plt.savefig("docs/images/data_flow.png", dpi=150, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    os.makedirs("docs/images", exist_ok=True)
    create_architecture_diagram()
    create_data_flow()
