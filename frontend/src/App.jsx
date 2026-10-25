import { useState, useEffect } from "react";
import {
    Shield,
    Upload,
    FileText,
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Scale,
    Lightbulb,
    BookOpen,
    Loader2,
    ChevronDown,
    ChevronUp,
    Search,
    Copy,
    Check
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
export default function App() {
    const [activeTab, setActiveTab] = useState("upload"); // 'upload' | 'single'
    const [serverStatus, setServerStatus] = useState({ online: false, lawsCount: 0 });

    // States for full contract analysis & progress bar
    const [selectedFile, setSelectedFile] = useState(null);
    const [isAnalyzingContract, setIsAnalyzingContract] = useState(false);
    const [contractReport, setContractReport] = useState(null);
    const [riskFilter, setRiskFilter] = useState("all"); // 'all' | 'red' | 'yellow' | 'green'
    const [progressText, setProgressText] = useState("");
    const [currentBatch, setCurrentBatch] = useState(0);
    const [totalBatches, setTotalBatches] = useState(0);

    // States for single clause analysis
    const [clauseInput, setClauseInput] = useState("");
    const [isAnalyzingClause, setIsAnalyzingClause] = useState(false);
    const [singleResult, setSingleResult] = useState(null);

    const [errorMsg, setErrorMsg] = useState("");

    // Check backend health on mount
    useEffect(() => {
        fetch(`${API_BASE_URL}/health`)
            .then((res) => res.json())
            .then((data) => {
                if (data.status === "healthy") {
                    setServerStatus({ online: true, lawsCount: data.indexed_law_clauses });
                }
            })
            .catch(() => setServerStatus({ online: false, lawsCount: 0 }));
    }, []);

    // Handle full contract file upload & analysis
    const handleAnalyzeContract = async () => {
        if (!selectedFile) return;
        setIsAnalyzingContract(true);
        setErrorMsg("");
        setContractReport(null);
        setProgressText("מעלה את החוזה לשרת...");
        setCurrentBatch(0);
        setTotalBatches(0);

        const progressInterval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/progress`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.message) {
                        setProgressText(data.message);
                    }
                    if (data.current_batch !== undefined) {
                        setCurrentBatch(data.current_batch);
                    }
                    if (data.total_batches !== undefined) {
                        setTotalBatches(data.total_batches);
                    }
                }
            } catch (e) {
                // התעלמות משגיאות רשת זמניות בזמן פולינג
            }
        }, 1000);

        const formData = new FormData();
        formData.append("file", selectedFile);

        try {
            const response = await fetch(`${API_BASE_URL}/analyze-contract`, {
                method: "POST",
                body: formData,
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "שגיאה בניתוח החוזה מול השרת");
            }

            const data = await response.json();
            setContractReport(data);
            setRiskFilter("all");
        } catch (err) {
            clearInterval(progressInterval);
            setErrorMsg(err.message);
        } finally {
            clearInterval(progressInterval);
            setIsAnalyzingContract(false);
            setProgressText("");
            setCurrentBatch(0);
            setTotalBatches(0);
        }
    };

    // Handle single clause analysis
    const handleAnalyzeSingleClause = async () => {
        if (!clauseInput.trim() || clauseInput.trim().length < 10) {
            setErrorMsg("אנא הזן סעיף חוזה באורך של לפחות 10 תווים.");
            return;
        }
        setIsAnalyzingClause(true);
        setErrorMsg("");
        setSingleResult(null);

        try {
            const response = await fetch(`${API_BASE_URL}/analyze-clause`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ clause_text: clauseInput }),
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "שגיאה בניתוח הסעיף");
            }

            const data = await response.json();
            setSingleResult(data);
        } catch (err) {
            setErrorMsg(err.message);
        } finally {
            setIsAnalyzingClause(false);
        }
    };

    const filteredResults = contractReport?.results.filter((item) =>
        riskFilter === "all" ? true : item.analysis.risk === riskFilter
    );

    const progressPercentage = totalBatches > 0 ? (currentBatch / totalBatches) * 100 : 0;

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Top Navbar */}
            <header className="bg-white border-b border-slate-200 sticky top-0 z-20">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-600 p-2.5 rounded-xl text-white shadow-sm">
                            <Shield className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                                Tenant Shield <span className="text-indigo-600">| מגן השוכר</span>
                            </h1>
                            <p className="text-xs text-slate-500">
                                מערכת RAG משפטית לבדיקת חוזי שכירות מול חוק השכירות והשאילה
                            </p>
                        </div>
                    </div>

                    {/* Backend & Vector DB Status Badge */}
                    <div className="flex items-center gap-2 bg-slate-100 px-3.5 py-1.5 rounded-full text-xs font-medium">
                        <span
                            className={`w-2.5 h-2.5 rounded-full ${
                                serverStatus.online ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
                            }`}
                        />
                        <span className="text-slate-700">
                            {serverStatus.online
                                ? `מאגר חקיקה פעיל (${serverStatus.lawsCount} סעיפי חוק)`
                                : "שרת ה-API מנותק"}
                        </span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-6xl w-full mx-auto px-6 py-8 flex-1">
                {/* Mode Selector Tabs */}
                <div className="flex gap-3 mb-8 bg-slate-200/70 p-1.5 rounded-xl w-fit">
                    <button
                        onClick={() => {
                            setActiveTab("upload");
                            setErrorMsg("");
                        }}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                            activeTab === "upload"
                                ? "bg-white text-indigo-600 shadow-sm"
                                : "text-slate-600 hover:text-slate-900"
                        }`}
                    >
                        <FileText className="w-4 h-4" />
                        ניתוח חוזה מלא (PDF / DOCX)
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab("single");
                            setErrorMsg("");
                        }}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all cursor-pointer ${
                            activeTab === "single"
                                ? "bg-white text-indigo-600 shadow-sm"
                                : "text-slate-600 hover:text-slate-900"
                        }`}
                    >
                        <Search className="w-4 h-4" />
                        בדיקת סעיף בודד
                    </button>
                </div>

                {/* Error Alert */}
                {errorMsg && (
                    <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
                        <AlertTriangle className="w-5 h-5 shrink-0" />
                        <span>{errorMsg}</span>
                    </div>
                )}

                {/* TAB 1: FULL CONTRACT UPLOAD */}
                {activeTab === "upload" && (
                    <div className="space-y-8">
                        <div className="bg-white border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-indigo-400 transition-colors">
                            <div className="bg-indigo-50 w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 text-indigo-600">
                                <Upload className="w-7 h-7" />
                            </div>
                            <h2 className="text-lg font-bold text-slate-800 mb-1">
                                העלה קובץ חוזה שכירות לבדיקה אוטומטית
                            </h2>
                            <p className="text-sm text-slate-500 mb-6">
                                תומך בקובצי PDF, Word (DOCX) או קובצי טקסט (TXT)
                            </p>

                            <label className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium px-5 py-2.5 rounded-xl cursor-pointer transition-colors text-sm">
                                <span>בחר קובץ מהמחשב</span>
                                <input
                                    type="file"
                                    accept=".pdf,.docx,.txt"
                                    className="hidden"
                                    onChange={(e) => setSelectedFile(e.target.files[0] || null)}
                                />
                            </label>

                            {selectedFile && (
                                <div className="mt-5 flex flex-col items-center gap-3 w-full">
                                    <span className="text-sm font-medium text-indigo-700 bg-indigo-50 px-4 py-1.5 rounded-full">
                                        📄 {selectedFile.name}
                                    </span>
                                    <button
                                        type="button"
                                        onClick={handleAnalyzeContract}
                                        disabled={isAnalyzingContract}
                                        className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-8 py-3 rounded-xl shadow-sm transition-all flex flex-col items-center gap-2 cursor-pointer w-full max-w-md mx-auto"
                                    >
                                        {isAnalyzingContract ? (
                                            <div className="flex flex-col items-center gap-1.5 py-1 w-full">
                                                <div className="flex items-center gap-2 justify-center">
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                    <span className="font-bold text-sm">מעבד חוזה מול מאגר החקיקה...</span>
                                                </div>
                                                <span className="text-xs text-indigo-100 font-normal">
                                                    {progressText}
                                                </span>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2">
                                                <Scale className="w-5 h-5" />
                                                <span>התחל ניתוח משפטי מלא</span>
                                            </div>
                                        )}
                                    </button>

                                    {/* Real-time Progress Bar */}
                                    {isAnalyzingContract && (
                                        <div className="w-full max-w-md mt-2 space-y-1.5">
                                            <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden shadow-inner">
                                                <div
                                                    className="bg-indigo-600 h-full transition-all duration-500 ease-out rounded-full"
                                                    style={{ width: `${progressPercentage}%` }}
                                                ></div>
                                            </div>
                                            <div className="flex justify-between text-xs text-slate-500 font-medium px-1">
                                                <span>מקבץ {currentBatch} מתוך {totalBatches || "?"}</span>
                                                <span>{Math.round(progressPercentage)}%</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Contract Analysis Dashboard */}
                        {contractReport && (
                            <div className="space-y-6">
                                {/* Summary Metric Cards (Clickable Filters) */}
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                                    <button
                                        onClick={() => setRiskFilter("all")}
                                        className={`p-5 rounded-2xl border text-right transition-all cursor-pointer ${
                                            riskFilter === "all"
                                                ? "bg-slate-900 text-white border-slate-900 shadow-md"
                                                : "bg-white border-slate-200 hover:border-slate-300"
                                        }`}
                                    >
                                        <p className="text-xs opacity-80">סה"כ סעיפים שנותחו</p>
                                        <p className="text-3xl font-extrabold mt-1">
                                            {contractReport.metrics.total_clauses}
                                        </p>
                                    </button>

                                    <button
                                        onClick={() => setRiskFilter("red")}
                                        className={`p-5 rounded-2xl border text-right transition-all cursor-pointer ${
                                            riskFilter === "red"
                                                ? "bg-rose-600 text-white border-rose-600 shadow-md"
                                                : "bg-rose-50/70 border-rose-200 text-rose-900 hover:bg-rose-100/70"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-semibold">סיכון גבוה / סותר חוק</span>
                                            <XCircle className="w-5 h-5 text-rose-500" />
                                        </div>
                                        <p className="text-3xl font-extrabold mt-1">
                                            {contractReport.metrics.red_count}
                                        </p>
                                    </button>

                                    <button
                                        onClick={() => setRiskFilter("yellow")}
                                        className={`p-5 rounded-2xl border text-right transition-all cursor-pointer ${
                                            riskFilter === "yellow"
                                                ? "bg-amber-500 text-white border-amber-500 shadow-md"
                                                : "bg-amber-50/70 border-amber-200 text-amber-900 hover:bg-amber-100/70"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-semibold">דורש הבהרה / גבולי</span>
                                            <AlertTriangle className="w-5 h-5 text-amber-500" />
                                        </div>
                                        <p className="text-3xl font-extrabold mt-1">
                                            {contractReport.metrics.yellow_count}
                                        </p>
                                    </button>

                                    <button
                                        onClick={() => setRiskFilter("green")}
                                        className={`p-5 rounded-2xl border text-right transition-all cursor-pointer ${
                                            riskFilter === "green"
                                                ? "bg-emerald-600 text-white border-emerald-600 shadow-md"
                                                : "bg-emerald-50/70 border-emerald-200 text-emerald-900 hover:bg-emerald-100/70"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="text-xs font-semibold">סעיפים תקינים</span>
                                            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                                        </div>
                                        <p className="text-3xl font-extrabold mt-1">
                                            {contractReport.metrics.green_count}
                                        </p>
                                    </button>
                                </div>

                                {/* Clause Cards List */}
                                <div className="space-y-4">
                                    {filteredResults.map((item, idx) => (
                                        <ClauseAnalysisCard key={idx} index={idx + 1} item={item} />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* TAB 2: SINGLE CLAUSE ANALYSIS */}
                {activeTab === "single" && (
                    <div className="space-y-6">
                        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
                            <label className="block text-sm font-bold text-slate-800 mb-2">
                                הדבק סעיף מתוך חוזה השכירות לבדיקה ממוקדת:
                            </label>
                            <textarea
                                rows={4}
                                value={clauseInput}
                                onChange={(e) => setClauseInput(e.target.value)}
                                placeholder="לדוגמה: השוכר יישא בעלות תיקון כל קלקול או בלאי במערכות הדירה, לרבות צנרת, דוד שמש ומזגנים..."
                                className="w-full rounded-xl border border-slate-300 p-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50"
                            />
                            <div className="mt-4 flex justify-end">
                                <button
                                    type="button"
                                    onClick={handleAnalyzeSingleClause}
                                    disabled={isAnalyzingClause}
                                    className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold px-6 py-2.5 rounded-xl transition-all flex items-center gap-2 text-sm cursor-pointer"
                                >
                                    {isAnalyzingClause ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            מנתח סעיף...
                                        </>
                                    ) : (
                                        <>
                                            <Scale className="w-4 h-4" />
                                            נתח סעיף מול החוק
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {singleResult && <ClauseAnalysisCard index={1} item={singleResult} defaultOpen />}
                    </div>
                )}
            </main>
        </div>
    );
}

/* Reusable Component for displaying a single analyzed clause */
function ClauseAnalysisCard({ index, item }) {
    const [showRawLaw, setShowRawLaw] = useState(false);
    const [isCopied, setIsCopied] = useState(false);
    const { analysis, clause_text, retrieved_context } = item;
    const risk = analysis.risk;

    const badgeStyles = {
        red: {
            bg: "bg-rose-50/70 border-rose-200",
            badge: "bg-rose-100 text-rose-700",
            label: "סיכון גבוה / סותר חוק",
            icon: <XCircle className="w-5 h-5 text-rose-600 shrink-0" />,
        },
        yellow: {
            bg: "bg-amber-50/60 border-amber-200",
            badge: "bg-amber-100 text-amber-800",
            label: "דורש הבהרה / גבולי",
            icon: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
        },
        green: {
            bg: "bg-white border-slate-200",
            badge: "bg-emerald-100 text-emerald-800",
            label: "תקין",
            icon: <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />,
        },
    }[risk] || {
        bg: "bg-white border-slate-200",
        badge: "bg-slate-100 text-slate-700",
        label: "נבדק",
        icon: null,
    };

    const handleCopyRevision = () => {
        if (!analysis.suggested_revision) return;
        navigator.clipboard.writeText(analysis.suggested_revision);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
    };

    return (
        <div className={`rounded-2xl border p-6 transition-all shadow-xs ${badgeStyles.bg}`}>
            {/* Header */}
            <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex items-center gap-3">
                    {badgeStyles.icon}
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-slate-400">סעיף #{index}</span>
                            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${badgeStyles.badge}`}>
                                {badgeStyles.label}
                            </span>
                        </div>
                        <h3 className="text-base font-bold text-slate-900 mt-1">{analysis.summary}</h3>
                    </div>
                </div>
                <span className="text-xs font-medium bg-indigo-50 text-indigo-700 px-3 py-1 rounded-lg border border-indigo-100 shrink-0">
                    ⚖️ {analysis.cited_laws}
                </span>
            </div>

            {/* Original Clause Box */}
            <div className="bg-slate-900/5 border border-slate-200/80 rounded-xl p-3.5 mb-5 text-xs text-slate-700 leading-relaxed">
                <span className="font-bold text-slate-900 block mb-1">נוסח הסעיף בחוזה:</span>
                "{clause_text}"
            </div>

            {/* Two-Column Reasoning & Recommendation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="bg-white/90 border border-slate-200/80 rounded-xl p-4">
                    <div className="flex items-center gap-2 font-bold text-slate-800 mb-1.5">
                        <Scale className="w-4 h-4 text-indigo-600" />
                        נימוק משפטי
                    </div>
                    <p className="text-slate-600 leading-relaxed text-xs">{analysis.legal_reasoning}</p>
                </div>

                <div className="bg-white/90 border border-slate-200/80 rounded-xl p-4">
                    <div className="flex items-center gap-2 font-bold text-slate-800 mb-1.5">
                        <Lightbulb className="w-4 h-4 text-amber-500" />
                        המלצה מעשית לשוכר
                    </div>
                    <p className="text-slate-600 leading-relaxed text-xs">{analysis.recommendation}</p>
                </div>
            </div>

            {/* Suggested Revision Box (Rendered only if provided) */}
            {analysis.suggested_revision && (
                <div className="mt-4 p-4 bg-indigo-50/80 border border-indigo-200 rounded-xl text-right">
                    <div className="flex justify-between items-center mb-2">
                        <button
                            type="button"
                            onClick={handleCopyRevision}
                            className={`text-xs font-medium px-3 py-1.5 rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs ${
                                isCopied
                                    ? "bg-emerald-600 text-white border-emerald-600"
                                    : "bg-white hover:bg-indigo-50 text-indigo-700 border-indigo-200 hover:border-indigo-300"
                            }`}
                        >
                            {isCopied ? (
                                <>
                                    <Check className="w-3.5 h-3.5 text-white" />
                                    <span>הועתק ללוח!</span>
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3.5 h-3.5" />
                                    <span>העתק נוסח</span>
                                </>
                            )}
                        </button>
                        <span className="text-xs font-bold text-indigo-950 flex items-center gap-1.5">
                            ✍️ הצעה לנוסח מתוקן לחתימה:
                        </span>
                    </div>
                    <p className="text-xs text-slate-800 leading-relaxed font-sans bg-white p-3 rounded-lg border border-indigo-100/80 shadow-2xs">
                        "{analysis.suggested_revision}"
                    </p>
                </div>
            )}

            {/* Expandable RAG Grounding Context */}
            {retrieved_context && (
                <div className="mt-4 pt-3 border-t border-slate-200/60">
                    <button
                        onClick={() => setShowRawLaw(!showRawLaw)}
                        className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 cursor-pointer"
                    >
                        <BookOpen className="w-3.5 h-3.5" />
                        <span>צפה בלשון החוק המקורית שנשלפה מ-ChromaDB (RAG Context)</span>
                        {showRawLaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {showRawLaw && (
                        <pre className="mt-3 bg-slate-900 text-slate-100 p-4 rounded-xl text-xs whitespace-pre-wrap font-sans leading-relaxed overflow-x-auto">
                            {retrieved_context}
                        </pre>
                    )}
                </div>
            )}
        </div>
    );
}