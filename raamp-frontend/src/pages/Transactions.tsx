import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, Download, FileText, Loader2 } from "lucide-react";
import { apiClient } from "@/services/api";
import { toast } from "sonner";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, fadeIn } from "@/utils/animations";

interface Invoice {
    id: string;
    date: number;
    description: string;
    amount: number;
    currency: string;
    status: string;
    invoice_pdf: string | null;
    hosted_invoice_url: string | null;
    type: string;
}

const Transactions = () => {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchInvoices = async () => {
            try {
                const res = await apiClient.get<{ invoices: Invoice[] }>("/stripe/invoices");
                setInvoices(res.invoices);
            } catch {
                toast.error("Failed to load transaction history");
            } finally {
                setLoading(false);
            }
        };
        fetchInvoices();
    }, []);

    const formatDate = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    const handleDownloadPdf = (invoice: Invoice) => {
        if (invoice.invoice_pdf) {
            window.open(invoice.invoice_pdf, "_blank");
        } else if (invoice.hosted_invoice_url) {
            window.open(invoice.hosted_invoice_url, "_blank");
        } else {
            toast.error("No invoice PDF available for this transaction");
        }
    };

    const handleExportCsv = () => {
        if (invoices.length === 0) {
            toast.error("No transactions to export");
            return;
        }
        const header = "Date,Description,Amount,Currency,Status\n";
        const rows = invoices.map(inv =>
            `${formatDate(inv.date)},"${inv.description}",${inv.type === "credit" ? "" : "-"}$${inv.amount.toFixed(2)},${inv.currency},${inv.status}`
        ).join("\n");
        const blob = new Blob([header + rows], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "raamp-transactions.csv";
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="min-h-screen bg-background">
            <nav className="border-b border-primary/10 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
                <Reveal variant="fadeInDown" duration={0.5} className="container mx-auto px-4">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/dashboard" className="flex items-center gap-2">
                            <motion.div
                                whileHover={{ rotate: 15, scale: 1.1 }}
                                className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center"
                            >
                                <Zap className="w-5 h-5 text-primary" />
                            </motion.div>
                            <span className="text-xl font-bold">RAAMP</span>
                        </Link>
                    </div>
                </Reveal>
            </nav>

            <main className="container mx-auto px-4 py-8">
                <div className="space-y-8 max-w-6xl mx-auto">
                    <div className="flex items-center justify-between">
                        <Reveal variant="blurInUp">
                            <div>
                                <h1 className="text-4xl font-bold mb-2">Transaction History</h1>
                                <p className="text-muted-foreground">
                                    View and download all your payment transactions
                                </p>
                            </div>
                        </Reveal>

                        <Reveal variant="fadeIn" delay={0.2}>
                            <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                <Button variant="outline" onClick={handleExportCsv} disabled={invoices.length === 0}>
                                    <Download className="w-4 h-4 mr-2" />
                                    Export CSV
                                </Button>
                            </motion.div>
                        </Reveal>
                    </div>

                    {loading ? (
                        <div className="flex items-center justify-center py-20">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        </div>
                    ) : invoices.length === 0 ? (
                        <Reveal variant="fadeInUp" delay={0.3}>
                            <Card className="card-shadow bg-card/70 backdrop-blur-sm border-primary/10 p-12 text-center">
                                <FileText className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
                                <h2 className="text-xl font-bold mb-2">No Transactions Yet</h2>
                                <p className="text-muted-foreground mb-4">
                                    Your payment history will appear here once you make a purchase or subscribe to a plan.
                                </p>
                                <Link to="/dashboard/billing">
                                    <Button variant="outline">View Plans</Button>
                                </Link>
                            </Card>
                        </Reveal>
                    ) : (
                        <>
                            <Reveal variant="fadeInUp" delay={0.3}>
                                <Card className="card-shadow bg-card/70 backdrop-blur-sm border-primary/10 overflow-hidden">
                                    <div className="overflow-x-auto">
                                        <table className="w-full">
                                            <thead className="bg-muted/50 border-b border-primary/10">
                                                <tr>
                                                    <th className="px-6 py-4 text-left text-sm font-bold">Date</th>
                                                    <th className="px-6 py-4 text-left text-sm font-bold">Description</th>
                                                    <th className="px-6 py-4 text-right text-sm font-bold">Amount</th>
                                                    <th className="px-6 py-4 text-center text-sm font-bold">Status</th>
                                                    <th className="px-6 py-4 text-center text-sm font-bold">Invoice</th>
                                                </tr>
                                            </thead>
                                            <motion.tbody
                                                className="divide-y divide-primary/10"
                                                variants={staggerContainer}
                                                initial="hidden"
                                                animate="visible"
                                            >
                                                {invoices.map((invoice) => (
                                                    <motion.tr
                                                        key={invoice.id}
                                                        variants={fadeInUp}
                                                        className="hover:bg-muted/30 transition-colors"
                                                    >
                                                        <td className="px-6 py-4 text-sm text-muted-foreground">
                                                            {formatDate(invoice.date)}
                                                        </td>
                                                        <td className="px-6 py-4">
                                                            <div className="flex items-center gap-3">
                                                                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                                                                    <FileText className="w-4 h-4 text-primary" />
                                                                </div>
                                                                <span className="text-sm font-medium">{invoice.description}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-6 py-4 text-right">
                                                            <span className={`text-sm font-bold ${invoice.type === "credit" ? "text-primary" : "text-foreground"}`}>
                                                                {invoice.type === "credit" ? "+" : "-"}${invoice.amount.toFixed(2)}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 text-center">
                                                            <Badge variant={invoice.status === "paid" ? "default" : "secondary"} className="text-xs">
                                                                {invoice.status}
                                                            </Badge>
                                                        </td>
                                                        <td className="px-6 py-4 text-center">
                                                            <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                                                <Button
                                                                    variant="ghost"
                                                                    size="sm"
                                                                    onClick={() => handleDownloadPdf(invoice)}
                                                                    disabled={!invoice.invoice_pdf && !invoice.hosted_invoice_url}
                                                                >
                                                                    <Download className="w-3 h-3 mr-1" />
                                                                    PDF
                                                                </Button>
                                                            </motion.div>
                                                        </td>
                                                    </motion.tr>
                                                ))}
                                            </motion.tbody>
                                        </table>
                                    </div>
                                </Card>
                            </Reveal>

                            <Reveal variant="fadeIn" delay={0.4}>
                                <p className="text-sm text-muted-foreground">
                                    Showing {invoices.length} transaction{invoices.length !== 1 ? "s" : ""}
                                </p>
                            </Reveal>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Transactions;