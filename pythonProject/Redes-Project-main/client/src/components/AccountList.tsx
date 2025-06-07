type Account = {
  id: string;
  name: string;
  number: string;
  balance: number;
};

interface AccountListProps {
  accounts: Account[];
}

export default function AccountList({ accounts }: AccountListProps) {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 text-center text-blue-800">Cuentas del Banco</h2>
      <div className="grid grid-cols-1 gap-4">
        {accounts.map((account) => (
          <div key={account.id} className="bg-white p-4 rounded-xl shadow-md border border-gray-200">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-gray-700">{account.name}</h3>
                <p className="text-sm text-gray-500">N° Cuenta: {account.number}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">Saldo:</p>
                <p className="text-xl font-bold text-green-600">₡{account.balance.toLocaleString()}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
