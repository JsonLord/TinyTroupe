# Spawning Sub-Agents and Implementing Hierarchies

A powerful capability of TinyTroupe is the ability to create complex, multi-agent workflows, such as a planner/worker hierarchy. In this model, a primary "planner" agent decomposes a large task and delegates sub-tasks to newly spawned "worker" agents that can operate in parallel. The existing framework provides all the necessary tools to implement this.

## Core Components for Building Hierarchies

### 1. Spawning (Cloning) Sub-Agents
Agents can be created dynamically during a simulation. The `TinyPerson` class includes a method specifically for this purpose: `create_new_agent_from_current_spec(new_name)`.

- **How it Works:** This method creates a new `TinyPerson` instance that is a clone of the original. It inherits the same persona, characteristics, and mental faculties, but is given a new, unique name. This is ideal for creating a team of worker agents that share a common skill set.

- **Example:**
  ```python
  # Assume 'planner_agent' is an existing TinyPerson

  # Spawn a new worker agent based on the planner's template
  worker_1 = planner_agent.create_new_agent_from_current_spec(new_name="Worker_1")

  # The new agent must be added to the environment to participate
  world.add_agent(worker_1)
  ```

### 2. Parallel Task Execution
The `TinyWorld` environment natively supports running agent actions in parallel. This is essential for a planner/worker model, as it allows all the worker agents to perform their tasks concurrently, dramatically speeding up the completion of the overall goal.

- **How it Works:** The `world.run()` method has a `parallelize` parameter. When set to `True`, the environment uses a thread pool to execute each agent's `act()` method simultaneously.

- **Example:**
  ```python
  # This will run the simulation for 5 steps, with all agents
  # in the world thinking and acting at the same time.
  world.run(steps=5, parallelize=True)
  ```

## Implementation Plan for a Planner/Worker Hierarchy

Here is a step-by-step guide to creating a simple planner/worker system.

### Step 1: Define the Planner Agent
Create a specialized planner agent. This agent should have a persona and mental faculties geared towards goal decomposition and task management. You could create a `PlanningFaculty` that helps it break down complex requests.

### Step 2: The Planner Decomposes the Goal
The planner receives a high-level goal via its `listen()` method.

- **Example Goal:** "Please write a market research report on the top 3 competitors in the electric vehicle industry."
- The planner's `act()` method, guided by its `PlanningFaculty`, would break this down into smaller, self-contained tasks:
  1. "Research and summarize the activities of Competitor A."
  2. "Research and summarize the activities of Competitor B."
  3. "Research and summarize the activities of Competitor C."
  4. "Synthesize the summaries into a final report."

### Step 3: Spawn and Delegate to Worker Agents
For each sub-task, the planner spawns a new worker agent and assigns it the task.

```python
# Planner's internal logic (inside its act() method)

tasks = ["Research Competitor A", "Research Competitor B", "Research Competitor C"]
worker_agents = []

for i, task in enumerate(tasks):
    # 1. Spawn the worker
    worker_name = f"Researcher_{i+1}"
    new_worker = self.create_new_agent_from_current_spec(new_name=worker_name)

    # 2. Add the worker to the world
    self.environment.add_agent(new_worker)
    worker_agents.append(new_worker)

    # 3. Delegate the task via a TALK action
    self.act(actions=[{
        "type": "TALK",
        "target": worker_name,
        "content": f"Your assignment is: {task}. Please return the summary to me when you are finished."
    }])
```

### Step 4: Workers Execute Tasks in Parallel
The `TinyWorld` now contains the planner and all the newly spawned worker agents. When `world.run(parallelize=True)` is called, the workers will receive their assignments and begin working on them concurrently.

### Step 5: Workers Report Back
Once a worker agent has completed its task, its final action would be to `TALK` to the planner and deliver the results.

- **Example Worker Action:**
  ```json
  {
    "type": "TALK",
    "target": "Planner_Agent",
    "content": "Here is the summary for Competitor A: [...]"
  }
  ```

### Step 6: Planner Synthesizes the Final Result
The planner agent's logic should include waiting to receive messages from all the worker agents. Once all the summaries have been collected, it can perform the final synthesis task to complete the original high-level goal.

This hierarchical approach is highly scalable and allows TinyTroupe to model complex, collaborative problem-solving scenarios.
