import { useState } from "react";
import AccountList from "./components/AccountList";
import Sidebar from "./components/Sidebar";

type Account = {
  id: string;
  name: string;
  number: string;
  balance: number;
};

function App() {
  const [accounts, setAccounts] = useState<Account[]>([]);

  const handleAddAccount = (newAccount: Omit<Account, "id">) => {
    setAccounts((prev) => [
      ...prev,
      { ...newAccount, id: Date.now().toString() },
    ]);
  };

  return (
    <>
      <div className="flex bg-gray-100 min-h-screen">
        <Sidebar onAdd={handleAddAccount} />
        <main className="ml-[300px] flex-1 p-6">
          <AccountList accounts={accounts} />
        </main>
      </div>
    </>
  );
}

export default App;
