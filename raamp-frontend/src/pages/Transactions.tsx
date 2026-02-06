import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Zap, Download, FileText } from "lucide-react";

// Animation Imports
import { motion } from "framer-motion";
import Reveal from "@/components/ui/Reveal";
import { staggerContainer, fadeInUp, hoverScale, blurInUp, fadeIn } from "@/utils/animations";

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
                                <Button variant="outline">
                                    <Download className="w-4 h-4 mr-2" />
                                    Export CSV
                                </Button>
                            </motion.div>
                        </Reveal>
                    </div>

                    <Reveal variant="fadeInUp" delay={0.3}>
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
                                    {/* Staggered Rows */}
                                    <motion.tbody
                                        className="divide-y divide-primary/10"
                                        variants={staggerContainer}
                                        initial="hidden"
                                        animate="visible"
                                    >
                                        {transactions.map((transaction, idx) => (
                                            <motion.tr
                                                key={idx}
                                                variants={fadeInUp}
                                                className="hover:bg-muted/30 transition-colors"
                                            >
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
                                                    <span className={`text-sm font-bold ${transaction.type === "credit" ? "text-primary" : "text-foreground"
                                                        }`}>
                                                        {transaction.amount}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-center">
                                                    <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                                                        <Button variant="ghost" size="sm">
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
                        <div className="flex items-center justify-between">
                            <p className="text-sm text-muted-foreground">
                                Showing {transactions.length} transactions
                            </p>
                            <div className="flex gap-2">
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button variant="outline" size="sm" disabled>
                                        Previous
                                    </Button>
                                </motion.div>
                                <motion.div variants={hoverScale} initial="rest" whileHover="hover" whileTap="tap">
                                    <Button variant="outline" size="sm" disabled>
                                        Next
                                    </Button>
                                </motion.div>
                            </div>
                        </div>
                    </Reveal>
                </div>
            </main>
        </div>
    );
};

export default Transactions;