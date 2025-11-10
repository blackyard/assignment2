# Restaurant Order Tracking — Transition from Python to Jac

This project showcases the evolution of a **restaurant order tracking system** originally implemented in **Python**, and later refactored into **Jac**, a graph-based and AI-native programming language.  

The transition highlights how procedural logic can be reimagined as autonomous, event-driven workflows with AI reasoning built in.

---

## Original Concept (Python)
The original Python implementation followed a **class-based approach**:
- A single `RestaurantOrder` class managed each order.
- Methods handled status updates, validation, and order history.
- The flow was **linear and procedural**, requiring explicit method calls and manual state updates.
- It worked well for simple, single-order tracking but became cumbersome when scaling to multiple concurrent orders or asynchronous logic.

### **Challenges in the Python version**
- Repetitive control flow for each order.
- Hard-coded transitions between order states.
- Limited interactivity and no built-in intelligence.
- Difficult to visualize or automate workflow progression.

---

## Transition to Jac
Jac reimagines the same order tracking logic using:
- **Graph-based architecture** — each order stage (PLACED, PREPARING, READY, DELIVERED) becomes a **node**.
- **Walkers (agents)** — autonomous entities that move through nodes, carrying contextual data such as item name and order ID.
- **LLM integration** — a built-in Gemini model (`gemini-2.0-flash`) dynamically generates contextual order messages.
- **Declarative flow** — order progression is defined through graph connections rather than procedural control statements.

---

## Conceptual Mapping: Python → Jac

| Concept | Python Implementation | Jac Implementation |
|----------|----------------------|--------------------|
| Order entity | Class (`RestaurantOrder`) | Walker (`OrderAgent`) |
| Status updates | Manual `update_status()` method | Autonomous graph traversal |
| Order states | List of strings | Connected graph nodes |
| Execution flow | Sequential, line-by-line | Event-driven, graph-based |
| State history | Manually stored timestamps | Implicit traversal context |
| AI logic | None | Built-in Gemini model via `by llm()` |
| Scalability | Single-order | Multi-agent capable |

---

## Advantages of Jac Implementation

### **1. Declarative Workflow**
Order stages are connected as nodes, defining how an order naturally progresses through its lifecycle.  
This eliminates manual “if/else” control and enhances readability.

### **2. Autonomous Agents**
Each order runs as its own *agent* (walker), capable of independently moving through stages.  
Multiple orders can be tracked simultaneously without complex threading.

### **3. AI-Powered Status Generation**
Jac’s `by llm()` functions allow integration with large language models (LLMs), enabling contextual status messages and intelligent decision-making directly within the workflow.

### **4. Visual and Scalable**
Workflows can be visualized as graphs and easily extended to handle:
- Parallel order processing
- Conditional branching (e.g., delayed or canceled orders)
- Notifications or dynamic updates via AI responses

---

## Execution Flow Overview
1. Define nodes representing each stage of an order: **PLACED → PREPARING → READY → DELIVERED**  
2. Initialize walkers (agents) for each order.  
3. Walkers traverse the graph autonomously, updating order stages and printing progress.  
4. Gemini model generates descriptive order updates in real-time.  
5. The process ends when all orders reach the **DELIVERED** node.

---

## Summary of the Transition

| Aspect | Python | Jac |
|---------|---------|-----|
| Programming Paradigm | Imperative (OOP) | Declarative (Graph-based) |
| Control Flow | Manual, step-by-step | Autonomous traversal |
| Extensibility | Limited | Scalable and concurrent |
| AI Integration | External / None | Native LLM interface |
| State Handling | Manual | Implicit graph context |
| Visualization | None | Graph visualization supported |

---

## Conclusion
This transition demonstrates how **Jac** simplifies and enriches application logic by:
- Abstracting procedural steps into connected workflows.  
- Enabling **autonomous, intelligent agents** instead of rigid classes.  
- Integrating AI reasoning directly within the logic layer.  

By moving from **Python’s object-oriented approach** to **Jac’s agent-based paradigm**, even simple systems like restaurant order tracking gain scalability, interactivity, and built-in intelligence ideal for real-time, multi-entity operations.

---
