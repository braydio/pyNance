# 🧮 Planning Module – Full Implementation Blueprint

This blueprint provides a **step-by-step guide** for implementing the Planning module in `pyNance`. It includes frontend, backend, and integration details with scaffolding instructions.

---

## 1. Current Status ✅

- Types, service stub, and composable implemented.
- Planning view scaffolded with route + navigation link.

---

## 2. Frontend Implementation

### 2.1 Components

Create components in `frontend/src/components/planning/`:

#### `BillForm.vue`

- **Purpose**: Create or edit a bill.
- **Fields**: name, amount, due date, frequency (weekly, monthly, yearly), category.
- **Emits**: `saveBill`, `cancel`.
- **Validation**: non-empty name, positive amount, valid date.

```vue
<template>
  <form @submit.prevent="onSubmit">
    <input v-model="bill.name" placeholder="Name" required />
    <input
      v-model.number="bill.amount"
      type="number"
      min="0"
      placeholder="Amount"
      required
    />
    <input v-model="bill.due_date" type="date" required />
    <select v-model="bill.frequency">
      <option value="monthly">Monthly</option>
      <option value="weekly">Weekly</option>
      <option value="yearly">Yearly</option>
    </select>
    <button type="submit">Save</button>
    <button type="button" @click="$emit('cancel')">Cancel</button>
  </form>
</template>
```

---

#### `BillList.vue`

- **Purpose**: Display and manage bills.
- **Features**: Edit, delete, mark paid.

```vue
<template>
  <ul>
    <li v-for="bill in bills" :key="bill.id">
      {{ bill.name }} - {{ bill.amount }} - Due: {{ bill.due_date }}
      <button @click="$emit('edit', bill)">Edit</button>
      <button @click="$emit('delete', bill.id)">Delete</button>
    </li>
  </ul>
</template>
```

---

#### `Allocator.vue`

- **Purpose**: Allocate percentages to categories.
- **Validation**: total must not exceed 100%.

```vue
<template>
  <div v-for="category in categories" :key="category">
    {{ category }}
    <input
      type="range"
      v-model.number="allocations[category]"
      min="0"
      max="100"
    />
    {{ allocations[category] }}%
  </div>
  <p>Total: {{ total }}%</p>
</template>
```

---

#### `PlanningSummary.vue`

- **Purpose**: Show summary of bills and allocations.

```vue
<template>
  <div>
    <h3>Planning Summary</h3>
    <p>Total Bills: {{ totalBills }}</p>
    <p>Remaining Cash: {{ remaining }}</p>
  </div>
</template>
```

---

### 2.2 Utilities

**`frontend/src/utils/currency.ts`**

```ts
export function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(
    value,
  );
}

export function convertCurrency(
  amount: number,
  from: string,
  to: string,
  rateTable: Record<string, number>,
): number {
  return (amount / rateTable[from]) * rateTable[to];
}
```

---

### 2.3 Services

**`frontend/src/services/planningService.ts`**

```ts
import axios from "axios";

export async function listBills() {
  return axios.get("/api/planning/bills");
}

export async function createBill(bill) {
  return axios.post("/api/planning/bills", bill);
}

export async function updateBill(id, bill) {
  return axios.put(`/api/planning/bills/${id}`, bill);
}

export async function deleteBill(id) {
  return axios.delete(`/api/planning/bills/${id}`);
}

export async function listAllocations() {
  return axios.get("/api/planning/allocations");
}

export async function updateAllocations(allocations) {
  return axios.put("/api/planning/allocations", allocations);
}
```

---

### 2.4 Tests

**`frontend/src/views/__tests__/Planning.cy.js`**

- Add bill → verify in list.
- Edit/delete bill.
- Allocation total enforcement.
- Summary calculation checks.

---

## 3. Backend Implementation

### 3.1 Routes

**`backend/app/routes/planning.py`**

```python
from fastapi import APIRouter
from backend.app.services import planning_service

router = APIRouter(prefix="/planning")

@router.get("/bills")
def list_bills():
    return planning_service.get_bills()

@router.post("/bills")
def create_bill(bill):
    return planning_service.create_bill(bill)

@router.put("/bills/{id}")
def update_bill(id: str, bill):
    return planning_service.update_bill(id, bill)

@router.delete("/bills/{id}")
def delete_bill(id: str):
    return planning_service.delete_bill(id)

@router.get("/allocations")
def list_allocations():
    return planning_service.get_allocations()

@router.put("/allocations")
def update_allocations(allocations):
    return planning_service.update_allocations(allocations)
```

---

### 3.2 Models

**`backend/app/models/planning.py`**

```python
from pydantic import BaseModel
from datetime import date

class Bill(BaseModel):
    id: str
    name: str
    amount: float
    due_date: date
    frequency: str
    category: str
    is_paid: bool = False

class Allocation(BaseModel):
    id: str
    category: str
    percentage: int
```

---

### 3.3 Service Layer

**`backend/app/services/planning_service.py`**

```python
bills = []
allocations = []

def get_bills():
    return bills

def create_bill(bill):
    bills.append(bill)
    return bill

def update_bill(id, bill):
    for i, b in enumerate(bills):
        if b.id == id:
            bills[i] = bill
            return bill
    return None

def delete_bill(id):
    global bills
    bills = [b for b in bills if b.id != id]
    return {"status": "deleted"}

def get_allocations():
    return allocations

def update_allocations(new_allocations):
    total = sum(a.percentage for a in new_allocations)
    if total > 100:
        raise ValueError("Total allocation cannot exceed 100%")
    allocations[:] = new_allocations
    return allocations
```

---

### 3.4 Tests

**`tests/test_api_planning.py`**

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_bill():
    response = client.post("/planning/bills", json={
        "id": "1",
        "name": "Credit Card Payment",
        "amount": 200,
        "due_date": "2025-09-15",
        "frequency": "monthly",
        "category": "debt"
    })
    assert response.status_code == 200


def test_allocation_cap():
    response = client.put("/planning/allocations", json=[
        {"id": "1", "category": "housing", "percentage": 60},
        {"id": "2", "category": "food", "percentage": 50}
    ])
    assert response.status_code == 400  # exceeds 100%
```

---

## 4. Integration

1. **Frontend ↔ Backend**: Connect `planningService.ts` to backend routes.
2. **Recurring Detection**: Auto-import recurring transactions into Planning.
3. **Dashboard**: Add “Upcoming Bills” + “Summary” widgets.

---

## 5. Future Enhancements

- Notifications/reminders before bill due dates.
- Multi-currency support.
- Export to CSV/PDF.
- AI-based prediction of future expenses.

---
