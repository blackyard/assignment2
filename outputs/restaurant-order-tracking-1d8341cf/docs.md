# 📘 Documentation for `restaurant-order-tracking-1d8341cf`

## 🧭 Project Overview

# Restaurant Order Tracking — Transition from Python to Jac

This project showcases the evolution of a **restaurant order tracking system** originally implemented in **Python**, and later refactored into **Jac**, a graph-based and AI-native programming language.  

The transition highlights how procedural logic can be reimagined as autonomous, event-driven workflows with AI reasoning built in.

---

## Original Concept (Python)
The original Python implementation followed a **class-based approach**:
## 🗂️ File Structure

<details><summary>Show file tree</summary>


```text
- .gitignore
- orders.jac
- orders.py
- README.md
```

</details>

## 📊 Code Context Graph

![CCG Diagram](outputs\restaurant-order-tracking-1d8341cf\ccg_networkx.svg)

<details><summary>Show Mermaid fallback</summary>


```mermaid
graph LR
%% Relationships: calls = -->, inherits = ==>, imports = -.->
  subgraph orders.jac
    orders.jac["orders.jac"]
  end
  subgraph orders.py
    orders.py["orders.py"]
  end
  orders.jac --> Model
  orders.jac --> OrderAgent
  orders.jac --> generate_order_status
  orders.jac --> input
  orders.jac --> llm
  orders.jac --> order_stage
  orders.jac --> print
  orders.py --> RestaurantOrder
  orders.py --> __init__
  orders.py --> append
  orders.py --> display_history
  orders.py --> get_status
  orders.py --> localtime
  orders.py --> print
  orders.py --> sleep
  orders.py --> strftime
  orders.py --> time
  orders.py --> update_status
```

</details>

## 🧪 API Reference

<details><summary>orders.jac</summary>


- Language: `jac`

- Relationships:

```json
{
  "calls": [
    "Model",
    "OrderAgent",
    "generate_order_status",
    "input",
    "llm",
    "order_stage",
    "print"
  ],
  "inherits": [],
  "functions": [],
  "classes": []
}
```

</details>

<details><summary>orders.py</summary>


- Language: `python`

- Relationships:

```json
{
  "calls": [
    "RestaurantOrder",
    "__init__",
    "append",
    "display_history",
    "get_status",
    "localtime",
    "print",
    "sleep",
    "strftime",
    "time",
    "update_status"
  ],
  "inherits": [],
  "functions": [
    "__init__",
    "display_history",
    "get_status",
    "update_status"
  ],
  "classes": [
    "RestaurantOrder"
  ]
}
```

</details>
