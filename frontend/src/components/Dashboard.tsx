import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Download, CheckCircle, LogOut, Activity, BarChart3, Database, Upload } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface StatusData {
  pending: number;
  success: number;
  failed: number;
  inProgress: number;
  total: number;
}

const Dashboard = () => {
  const [hasRequestedData, setHasRequestedData] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleFetchData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/invoices/import', { method: 'POST' });
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      setHasRequestedData(true);
      setCurrentStatus('Pending');
      toast({ title: 'تم بدء عملية جلب البيانات', description: `تم إدراج ${data.inserted} فاتورة جديدة` });
    } catch (e) {
      toast({ variant: 'destructive', title: 'فشل جلب البيانات', description: 'تأكد من تشغيل الخادم الخلفي' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleImportDbisam = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/dbisam/import', { method: 'POST' });
      if (!res.ok) throw new Error('failed');
      const stats = await res.json() as Record<string, number>;
      toast({ title: 'تم الاستيراد من قاعدة DBISAM', description: `الحسابات: ${stats.accounts} | العناصر: ${stats.items}` });
    } catch (e) {
      toast({ variant: 'destructive', title: 'فشل استيراد DBISAM', description: 'تأكد من تشغيل الخادم الخلفي ووجود ملفات data' });
    } finally {
      setIsLoading(false);
    }
  };



  const handleZakatProcess = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/invoices/zakat/process?simulate=true', { method: 'POST' });
      if (!res.ok) throw new Error('failed');
      const data = await res.json() as { processed: number; success: number; failed: number };
      toast({ title: 'تمت المعالجة نحو زاتكا (محاكاة)', description: `المعالَجة: ${data.processed} | نجاح: ${data.success} | فشل: ${data.failed}` });
    } catch (e) {
      toast({ variant: 'destructive', title: 'فشل معالجة زاتكا', description: 'تحقق من الخادم والإعدادات' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/invoices/stats');
      if (!res.ok) throw new Error('failed');
      const stats = await res.json() as Record<string, number>;
      const mapped: StatusData = {
        pending: stats['pending'] || 0,
        inProgress: stats['in_progress'] || 0,
        success: stats['done'] || 0,
        failed: stats['failed'] || 0,
        total: (stats['pending'] || 0) + (stats['in_progress'] || 0) + (stats['done'] || 0) + (stats['failed'] || 0),
      };
      setStatusData(mapped);
      toast({ title: 'تم جلب البيانات بنجاح', description: `إجمالي العمليات: ${mapped.total}` });
    } catch (error) {
      toast({ variant: 'destructive', title: 'خطأ في جلب البيانات', description: 'تعذر الاتصال بالخادم' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    toast({
      title: "تم تسجيل الخروج",
      description: "شكراً لاستخدامك نظام زاتكا",
    });
    navigate("/");
  };

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case "Success": return "bg-success text-success-foreground";
      case "In Progress": return "bg-primary text-primary-foreground";
      case "Filed": return "bg-accent text-accent-foreground";
      case "Pending": return "bg-warning text-warning-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  const getStatusArabic = (status: string | null) => {
    const statusMap = {
      "Pending": "في الانتظار",
      "In Progress": "قيد التنفيذ",
      "Filed": "تم الإيداع", 
      "Success": "تم بنجاح"
    };
    return status ? statusMap[status as keyof typeof statusMap] : "";
  };

  const getPieChartData = () => {
    if (!statusData) return [];
    
    return [
      { name: "في الانتظار", value: statusData.pending, color: "hsl(var(--warning))" },
      { name: "تم بنجاح", value: statusData.success, color: "hsl(var(--success))" },
      { name: "فشل", value: statusData.failed, color: "hsl(var(--destructive))" },
      { name: "قيد التنفيذ", value: statusData.inProgress, color: "hsl(var(--primary))" }
    ];
  };

  return (
    <div className="min-h-screen bg-gradient-elegant">
      {/* Header */}
      <header className="bg-card shadow-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
                <Activity className="w-6 h-6 text-primary-foreground" />
              </div>
              <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Zatca Dashboard
              </h1>
            </div>
            
            <Button 
              variant="outline" 
              onClick={handleLogout}
              className="flex items-center space-x-2 transition-smooth hover:shadow-button"
            >
              <LogOut className="w-4 h-4" />
              <span>تسجيل الخروج</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Welcome Card */}
          <Card className="bg-gradient-card shadow-elegant border-0">
            <CardHeader>
              <CardTitle className="text-2xl text-foreground">مرحباً بك في لوحة تحكم زاتكا</CardTitle>
              <CardDescription className="text-muted-foreground">
                يمكنك من هنا إدارة عمليات جلب البيانات ومتابعة حالة العمليات
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Status Card */}
          {currentStatus && (
            <Card className="bg-gradient-card shadow-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>حالة العملية الحالية</span>
                  <Badge className={`${getStatusColor(currentStatus)} px-3 py-1`}>
                    {getStatusArabic(currentStatus)}
                  </Badge>
                </CardTitle>
              </CardHeader>
            </Card>
          )}

          {/* Action Cards */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Fetch Data Card */}
            <Card className="bg-gradient-card shadow-card border-border transition-smooth hover:shadow-elegant">
              <CardHeader>
                <CardTitle className="flex items-center space-x-3">
                  <Download className="w-6 h-6 text-primary" />
                  <span>جلب البيانات</span>
                </CardTitle>
                <CardDescription>
                  ابدأ عملية جلب البيانات من النظام
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleFetchData}
                  disabled={isLoading}
                  className="w-full h-12 bg-gradient-primary text-primary-foreground shadow-button hover:shadow-elegant transition-bounce disabled:opacity-50"
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                      <span>جاري الحصول على البيانات...</span>
                    </div>
                  ) : (
                    "الحصول علي البيانات"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Check Status Card */}
            <Card className="bg-gradient-card shadow-card border-border transition-smooth hover:shadow-elegant">
              <CardHeader>
                <CardTitle className="flex items-center space-x-3">
                  <CheckCircle className="w-6 h-6 text-accent" />
                  <span>فحص الحالة</span>
                </CardTitle>
                <CardDescription>
                  جلب إحصائيات جميع العمليات
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleCheckStatus}
                  disabled={isLoading}
                  variant="outline"
                  className="w-full h-12 border-accent text-accent hover:bg-accent hover:text-accent-foreground transition-bounce disabled:opacity-50"
                >
                  {isLoading ? (
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                      <span>جاري جلب البيانات...</span>
                    </div>
                  ) : (
                    "جلب جميع الإحصائيات"
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* DBISAM Import Card */}
            <Card className="bg-gradient-card shadow-card border-border transition-smooth hover:shadow-elegant">
              <CardHeader>
                <CardTitle className="flex items-center space-x-3">
                  <Database className="w-6 h-6 text-muted-foreground" />
                  <span>استيراد DBISAM</span>
                </CardTitle>
                <CardDescription>
                  استيراد ملفات CSV من مجلد data إلى قاعدة منفصلة
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleImportDbisam}
                  disabled={isLoading}
                  variant="secondary"
                  className="w-full h-12 transition-bounce disabled:opacity-50"
                >
                  استيراد DBISAM
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* ZATCA Process Card */}
            <Card className="bg-gradient-card shadow-card border-border transition-smooth hover:shadow-elegant">
              <CardHeader>
                <CardTitle className="flex items-center space-x-3">
                  <Upload className="w-6 h-6 text-muted-foreground" />
                  <span>معالجة زاتكا</span>
                </CardTitle>
                <CardDescription>
                  توليد ورفع XML (محاكاة حالياً)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleZakatProcess}
                  disabled={isLoading}
                  variant="secondary"
                  className="w-full h-12 transition-bounce disabled:opacity-50"
                >
                  تشغيل معالجة زاتكا
                </Button>
              </CardContent>
            </Card>

          {statusData && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Numbers Card */}
              <Card className="bg-gradient-card shadow-card border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-3">
                    <BarChart3 className="w-6 h-6 text-primary" />
                    <span>إحصائيات العمليات</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-warning/10 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-warning">{statusData.pending}</div>
                      <div className="text-sm text-muted-foreground">في الانتظار</div>
                    </div>
                    <div className="bg-primary/10 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{statusData.inProgress}</div>
                      <div className="text-sm text-muted-foreground">قيد التنفيذ</div>
                    </div>
                    <div className="bg-success/10 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-success">{statusData.success}</div>
                      <div className="text-sm text-muted-foreground">تم بنجاح</div>
                    </div>
                    <div className="bg-destructive/10 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-destructive">{statusData.failed}</div>
                      <div className="text-sm text-muted-foreground">فشل</div>
                    </div>
                  </div>
                  <div className="border-t pt-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-foreground">{statusData.total}</div>
                      <div className="text-sm text-muted-foreground">إجمالي العمليات</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Pie Chart Card */}
              <Card className="bg-gradient-card shadow-card border-border">
                <CardHeader>
                  <CardTitle>النسب المئوية</CardTitle>
                  <CardDescription>توزيع العمليات حسب الحالة</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={getPieChartData()}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={120}
                          paddingAngle={5}
                          dataKey="value"
                        >
                          {getPieChartData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value: number) => [
                            `${value} (${((value / statusData.total) * 100).toFixed(1)}%)`,
                            'العدد'
                          ]}
                          labelStyle={{ color: 'hsl(var(--foreground))' }}
                          contentStyle={{ 
                            backgroundColor: 'hsl(var(--background))',
                            border: '1px solid hsl(var(--border))',
                            borderRadius: '6px'
                          }}
                        />
                        <Legend 
                          wrapperStyle={{ fontSize: '14px' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Info Card */}
          <Card className="bg-muted/50 border-border">
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground">
                <p className="text-sm">
                  نظام زاتكا للفوترة الإلكترونية - الإصدار 1.0
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;