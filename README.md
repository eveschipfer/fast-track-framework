# 🚀 Fast-Track Framework

> **Stop fighting entropy. Build scalable backends with architectural governance.**

FastAPI is excellent at **handling HTTP**.
Fast-Track exists to **govern systems that need to last**.

Fast-Track is an **architectural-grade, IoC-first framework** built on top of FastAPI for teams that have felt the real cost of **Python architectural entropy**.

If you've ever lost velocity trying to figure out *where* business logic belongs, *who* depends on *whom*, or *why* one endpoint breaks another… this framework is not an experiment. It's a solution.

---

## 🧠 The Problem Fast-Track Solves

### The Entropy Problem

FastAPI solves the **how** of HTTP.
It deliberately does not solve the **where** of business logic.

This “architectural freedom” works fine… until:

* rules start leaking into controllers
* dependencies become implicit
* tests require half the application running
* code becomes a **well-typed Big Ball of Mud**

Fast-Track imposes **architectural discipline before the mess begins**.

It transforms:

* implicit dependencies → **explicit, auditable contracts**
* implicit flow → **auditable pipeline**
* “works” code → **governable code**

---

## 🛡️ Competitive Advantage

| Dimension                         | Fast-Track                                                    | Vanilla FastAPI                                                       |
| --------------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------- |
| Architecture                      | IoC-first, opinionated by design                              | Left to the developer                                                 |
| Dependencies                      | Explicit and auditable                                        | Implicit                                                              |
| Scalability                       | Structural                                                    | Accidental                                                            |
| Maintainability                   | Predictable                                                   | Increasingly chaotic                                                  |
| Testability                       | High, by contract                                             | Fragmented                                                            |
| **Total Cost of Ownership (TCO)** | **Low TCO (Standardized stack, easy onboarding for seniors)** | **High TCO (Fragmented patterns, high cognitive load for new hires)** |

Fast-Track doesn’t compete with FastAPI.
It **fills the architectural gap** that appears after the MVP.

---

## 🧠 Mental Model: Governed Pipeline

In Fast-Track, a request **is not just a JSON hitting an endpoint**.

It’s an **object flowing through a governed pipeline**:

```
HTTP Request
   ↓
Guards (Auth / Authorization)
   ↓
Providers (IoC Container)
   ↓
Request Object (Validation + Intent)
   ↓
Use Case (Business Logic)
   ↓
Response
```

Nothing happens by accident.
Nothing depends on magic imports.
Nothing runs outside its contract.

This pipeline enables:

* true domain isolation
* infrastructure-free testing
* refactors without domino effects

---

## 🔥 Show, Don’t Tell — IoC in Action

```python
class StoreUserRequest(Request):
    email: EmailStr
    password: str

    async def handle(self, user_service: UserService):
        return await user_service.create_user(self.email, self.password)
```

This is **not syntactic sugar**:

* `Request` defines **intent**
* `UserService` is resolved via **IoC Container**
* no dependency is hidden
* the Use Case is **testable in isolation**
* controller becomes a transport detail

This isn’t “the Python way”.
It’s **software engineering applied to Python**.

---

## 💾 Eloquent ORM – Laravel-style, IoC-first

Fast-Track ships with an **ORM inspired by Laravel Eloquent**, designed for **Python async ecosystems**:

* **Fluent Queries:** chainable, readable, intuitive.
* **Relationships:** `hasOne`, `hasMany`, `belongsTo`, `manyToMany`—all async-ready.
* **IoC-integrated Models:** inject services, policies, and validators directly into models.
* **Migration & Schema Management:** fully declarative and versioned.
* **Observers & Hooks:** lifecycle events (`creating`, `updating`, `deleting`) for domain rules.
* **Query Scopes & Reusable Filters:** centralize business logic at the model layer, not in controllers.

```python
# Example: Eloquent-style async query
users = await User.where('status', 'active') \
                  .with('posts') \
                  .order_by('created_at', desc=True) \
                  .get()
```

This ORM **is not just sugar** — it’s an **architectural-first database layer** that plays nicely with Fast-Track pipelines, guards, and IoC container.
**The power of Eloquent, engineered for the constraints of high-performance async Python.**

---

## 📌 Read This First (Strategic Gatekeeping)

Fast-Track assumes **Architectural Discipline**.

You **must** understand:

* IoC / Dependency Injection
* Separation of Concerns
* Explicit Boundaries
* Why “magic” accrues high interest

Reading the documentation **is not optional**.
The framework is simple — your system probably isn’t.

---

## ❌ Choose FastAPI Instead If:

Choose **vanilla FastAPI** if you:

* want maximum speed for scripts or POCs
* prefer ad-hoc architectural decisions
* don’t value explicit contracts
* think “we’ll organize it later”

Fast-Track is binary:

> Either you want governance, or you want fast-and-loose.

---

## 🧭 Philosophy

* **IoC-first** (not IoC “when convenient”)
* Explicit > Implicit
* Architecture as an asset, not overhead
* Framework as guardrail, not playground

If you come from **Laravel, Symfony, Spring, ASP.NET**,
Fast-Track will feel… familiar.
If that bothers you, perfect — the filter worked.

---

## ▶️ Call to Action

If you’re building something that **must survive its own success**:

* Read the documentation
* Understand the pipeline
* Embrace governance

Fast-Track doesn’t accelerate shortcuts.
It **eliminates future rework**.
