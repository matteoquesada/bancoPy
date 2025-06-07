import React, { useState } from "react";

interface Props {
  onAdd: (account: { name: string; number: string; balance: number }) => void;
}

export default function Sidebar({ onAdd }: Props) {
  const [name, setName] = useState("");
  const [number, setNumber] = useState("");
  const [balance, setBalance] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !number || isNaN(Number(balance))) return;

    onAdd({ name, number, balance: Number(balance) });

    // Limpiar campos
    setName("");
    setNumber("");
    setBalance("");
  };

  return (
    <aside className="w-full max-w-xs bg-white p-6 border-r border-gray-200 h-screen fixed left-0 top-0 shadow-md">
      <h2 className="text-xl font-bold text-blue-700 mb-4">Crear Cuenta</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Nombre</label>
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Número de cuenta</label>
          <input
            type="text"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Saldo inicial</label>
          <input
            type="number"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            value={balance}
            onChange={(e) => setBalance(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white font-semibold py-2 rounded-md hover:bg-blue-700 transition"
        >
          Agregar Cuenta
        </button>
      </form>
    </aside>
  );
}
