import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, Download, FileText } from "lucide-react";

const Transactions = () => {
  const transactions = [
    { date: "2024-07-25", description: "RAAMP Monthly Subscription", amount: "-$499.00", type: "debit" },
    { date: "2024-07-20", description: "Geo-Intent Engine Data Pack (Premium)", amount: "-$120.00", type: "debit" },
    { date: "2024-07-18", description: "Creative Studio Asset Purchase", amount: "-$50.00", type: "debit" },
    { date: "2024-07-15", description: "Account Top-up via Credit Card", amount: "$500.00", type: "credit" },
    { date: "2024-07-10", description: "A/B Auto-Optimization Upgrade", amount: "-$99.00", type: "debit" },
    { date: "2024-07-05", description: "RAAMP Assistant Premium Access", amount: "-$75.00", type: "debit" },
    { date: "2024-07-01", description: "Initial Account Setup Fee", amount: "-$25.00", type: "debit" }
  ];

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary" />
              </div>
              <span className="text-xl font-bold">RAAMP</span>
            </Link>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8 max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">Transaction History</h1>
              <p className="text-muted-foreground">
                View and download all your payment transactions
              </p>
            </div>
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>

          <Card className="card-shadow bg-card/70 backdrop-blur-sm border-primary/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted/50 border-b border-primary/10">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-bold">Date</th>
                    <th className="px-6 py-4 text-left text-sm font-bold">Description</th>
                    <th className="px-6 py-4 text-right text-sm font-bold">Amount</th>
                    <th className="px-6 py-4 text-center text-sm font-bold">Invoice</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-primary/10">
                  {transactions.map((transaction, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {transaction.date}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                            <FileText className="w-4 h-4 text-primary" />
                          </div>
                          <span className="text-sm font-medium">{transaction.description}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`text-sm font-bold ${
                          transaction.type === "credit" ? "text-primary" : "text-foreground"
                        }`}>
                          {transaction.amount}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <Button variant="ghost" size="sm">
                          <Download className="w-3 h-3 mr-1" />
                          PDF
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {transactions.length} transactions
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled>
                Previous
              </Button>
              <Button variant="outline" size="sm" disabled>
                Next
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Transactions;
