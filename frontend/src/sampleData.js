export const sampleClients = [
  {
    id: "c1",
    name: "Alice Active",
    joinDate: new Date(new Date().setDate(new Date().getDate() - 15)).toISOString().slice(0,10),
    email: "alice@example.com",
    phone: "555-0001"
  },
  {
    id: "c2", 
    name: "Oscar Overdue",
    joinDate: new Date(new Date().setDate(new Date().getDate() - 100)).toISOString().slice(0,10), // 100 days ago to ensure overdue
    email: "oscar@example.com",
    phone: "555-0002"
  }
];