import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { complaintService, Complaint } from "@/services/complaintService";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  MessageSquare, 
  Send, 
  ShieldAlert, 
  User, 
  Mail, 
  Phone,
  ArrowRight,
  LifeBuoy
} from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import Navigation from "@/components/Navigation";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Separator } from "@/components/ui/separator";

const Complaints = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  // Form State
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");

  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Complaints & Support", active: true }
  ];

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const data = await complaintService.getUserComplaints();
      setComplaints(data.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()));
    } catch (error) {
      console.error("Failed to fetch complaints:", error);
      toast.error("Failed to load your complaints");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      setSubmitting(true);
      const response = await complaintService.submitComplaint({
        subject: subject.trim(),
        description: description.trim(),
        priority
      });
      
      toast.success("Complaint Submitted", {
        description: `Your complaint ID is ${response.id.substring(0, 8)}. We've sent an acknowledgement email.`
      });
      
      // Reset form
      setSubject("");
      setDescription("");
      setPriority("medium");
      
      // Refresh list
      fetchComplaints();
    } catch (error) {
      toast.error("Submission failed", {
        description: "We couldn't submit your complaint. Please try again later."
      });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
      case "in_progress":
      case "in progress":
        return <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20"><Clock className="w-3 h-3 mr-1" /> In Progress</Badge>;
      case "resolved":
        return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20"><CheckCircle2 className="w-3 h-3 mr-1" /> Resolved</Badge>;
      case "rejected":
        return <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20"><AlertCircle className="w-3 h-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      
      <main className={`flex-1 flex flex-col transition-all duration-300 ${collapsed ? "ml-20" : "ml-60"}`}>
        <Navigation title="Complaints & Support" />
        
        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 scrollbar-thin">
          <div className="max-w-6xl mx-auto space-y-8">
            <Breadcrumbs items={breadcrumbItems} />
            
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Support Center</h1>
                <p className="text-muted-foreground mt-1">Submit technical issues or track existing support requests.</p>
              </div>
              
              <div className="flex items-center gap-3">
                <Card className="bg-foreground/5 border-border/50 p-2 px-4 h-12 flex items-center gap-3">
                  <div className="flex items-center gap-2 text-xs font-medium">
                    <Mail className="w-3.5 h-3.5 text-primary" />
                    <span>support@raamp.ai</span>
                  </div>
                  <Separator orientation="vertical" className="h-4" />
                  <div className="flex items-center gap-2 text-xs font-medium">
                    <Phone className="w-3.5 h-3.5 text-primary" />
                    <span>+1 (800) RAAMP-AI</span>
                  </div>
                </Card>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Submission Form */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="lg:col-span-1"
              >
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm sticky top-0">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <LifeBuoy className="w-5 h-5 text-primary" />
                      New Complaint
                    </CardTitle>
                    <CardDescription>File a formal record of your issue.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Subject ⭐</label>
                        <Input 
                          placeholder="Brief subject of your complaint"
                          value={subject}
                          onChange={(e) => setSubject(e.target.value)}
                          className="bg-background/50 border-border/50 focus:border-primary/50"
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Description ⭐</label>
                        <Textarea 
                          placeholder="Describe the issue in detail. If it happened on a specific page, please mention it."
                          className="min-h-[200px] bg-background/50 border-border/50 focus:border-primary/50 resize-none"
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Priority</label>
                        <div className="flex gap-2">
                          {["low", "medium", "high"].map((p) => (
                            <Button
                              key={p}
                              type="button"
                              variant={priority === p ? "default" : "outline"}
                              size="sm"
                              onClick={() => setPriority(p)}
                              className="capitalize flex-1 h-9"
                            >
                              {p}
                            </Button>
                          ))}
                        </div>
                      </div>

                      <Button 
                        type="submit" 
                        className="w-full mt-6 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold h-11"
                        disabled={submitting}
                      >
                        {submitting ? "Submitting..." : (
                          <>
                            Submit Complaint
                            <Send className="w-4 h-4 ml-2" />
                          </>
                        )}
                      </Button>
                    </form>
                  </CardContent>
                  <CardFooter className="pt-0 flex flex-col items-start bg-foreground/5 p-4 rounded-b-xl border-t border-border/10">
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Authenticated As</p>
                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center">
                        <User className="w-3 h-3 text-primary" />
                      </div>
                      <span className="text-xs font-medium">{user?.email}</span>
                    </div>
                  </CardFooter>
                </Card>
              </motion.div>

              {/* Complaints List/History */}
              <div className="lg:col-span-2 space-y-6">
                <Tabs defaultValue="all" className="w-full">
                  <div className="flex items-center justify-between mb-4">
                    <TabsList className="bg-foreground/5 border border-border/50">
                      <TabsTrigger value="all">Recent Issues</TabsTrigger>
                      <TabsTrigger value="pending">Open</TabsTrigger>
                      <TabsTrigger value="resolved">Resolved</TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="all" className="space-y-4">
                    <AnimatePresence mode="popLayout">
                      {loading ? (
                        <div className="flex items-center justify-center p-12">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                        </div>
                      ) : complaints.length === 0 ? (
                        <Card className="border-dashed border-border/50 bg-transparent text-center p-12">
                          <div className="bg-foreground/5 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <MessageSquare className="w-6 h-6 text-muted-foreground" />
                          </div>
                          <h3 className="text-lg font-semibold">No complaints found</h3>
                          <p className="text-muted-foreground text-sm max-w-[250px] mx-auto mt-1">If you have an issue, use the form on the left to file a record.</p>
                        </Card>
                      ) : (
                        complaints.map((complaint, idx) => (
                          <motion.div
                            key={complaint.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                          >
                            <Card className="border-border/50 bg-card/30 hover:bg-card/50 transition-colors group">
                              <CardHeader className="pb-3">
                                <div className="flex justify-between items-start">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                      <h3 className="font-bold text-lg">{complaint.subject}</h3>
                                      <Badge variant="outline" className="text-[10px] opacity-70">
                                        #{complaint.id.substring(0, 8)}
                                      </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      Submitted on {new Date(complaint.createdAt).toLocaleDateString()} at {new Date(complaint.createdAt).toLocaleTimeString()}
                                    </p>
                                  </div>
                                  {getStatusBadge(complaint.status)}
                                </div>
                              </CardHeader>
                              <CardContent className="pb-4">
                                <p className="text-sm text-foreground/80 line-clamp-2 italic">"{complaint.description}"</p>
                                
                                {complaint.adminResponse && (
                                  <div className="mt-4 p-4 rounded-lg bg-primary/10 border border-primary/20">
                                    <div className="flex items-center gap-2 mb-2">
                                      <ShieldAlert className="w-4 h-4 text-primary" />
                                      <span className="text-xs font-bold text-primary uppercase tracking-wider">RAAMP Support Response</span>
                                    </div>
                                    <p className="text-sm font-medium">{complaint.adminResponse}</p>
                                  </div>
                                )}
                              </CardContent>
                              <CardFooter className="pt-0 flex justify-between border-t border-border/10 mt-2 p-4">
                                <div className="flex items-center gap-3">
                                  <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                    <AlertCircle className="w-3 h-3" />
                                    Priority: {complaint.priority}
                                  </div>
                                </div>
                                <Button variant="ghost" size="sm" className="h-7 text-xs flex items-center gap-1 group-hover:text-primary transition-colors">
                                  View History <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-1" />
                                </Button>
                              </CardFooter>
                            </Card>
                          </motion.div>
                        ))
                      )}
                    </AnimatePresence>
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Complaints;
