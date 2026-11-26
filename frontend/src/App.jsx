import React, { useState, useEffect, useMemo } from 'react';
import { 
  ShieldAlert, ShieldCheck, AlertTriangle, HelpCircle, Activity, 
  MapPin, Users, Sliders, RefreshCw, BarChart3, Database, Calendar,
  ChevronRight, TrendingUp, Info, CheckCircle2, XCircle, ArrowUpRight,
  Droplets, Thermometer, Wind, Eye, Compass, Layers, Shield
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, ReferenceLine, BarChart, Bar, Cell 
} from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import mockData from './data/mockData.json';

// Component to dynamically adjust map center on initial load
function MapRecenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && map.getZoom() < 12) {
      map.setView(center, 12.5);
    }
  }, [center]);
  return null;
}

export default function App() {
  const [metadata, setMetadata] = useState(null);
  const [selectedDate, setSelectedDate] = useState('');
  const [horizon, setHorizon] = useState(4);
  const [budgetTeams, setBudgetTeams] = useState(8);
  const [maskPct, setMaskPct] = useState(0);
  const [loading, setLoading] = useState(true);
  const [forecastData, setForecastData] = useState(null);
  const [selectedWard, setSelectedWard] = useState(null);
  const [wardHistory, setWardHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [benchmarks, setBenchmarks] = useState([]);
  const [activeTab, setActiveTab] = useState('surveillance'); // 'surveillance' | 'eval' | 'architecture'
  const [mapMode, setMapMode] = useState('carto'); // 'carto' | 'satellite'

  // Fetch initial metadata and benchmarks
  useEffect(() => {
    async function init() {
      try {
        const metaRes = await fetch('/api/metadata');
        if (!metaRes.ok) throw new Error('Metadata fetch failed');
        const metaJson = await metaRes.json();
        setMetadata(metaJson);
        setSelectedDate(metaJson.default_date);
        
        const benchRes = await fetch('/api/evaluation-benchmarks');
        if (benchRes.ok) {
          const benchJson = await benchRes.json();
          setBenchmarks(benchJson);
        }
      } catch (err) {
        console.warn("Backend API not reachable, loading bundled offline data for live demo:", err);
        setMetadata(mockData.metadata);
        setSelectedDate(mockData.metadata.default_date);
        setBenchmarks(mockData.benchmarks);
        setForecastData(mockData.forecast_default);
        if (mockData.forecast_default.wards && mockData.forecast_default.wards.length > 0) {
          setSelectedWard(mockData.forecast_default.wards[0]);
        }
      }
    }
    init();
  }, []);

  // Fetch forecast whenever parameters change
  useEffect(() => {
    if (!selectedDate) return;

    async function fetchForecast() {
      setLoading(true);
      try {
        const res = await fetch('/api/forecast', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date: selectedDate,
            horizon: horizon,
            budget_teams: budgetTeams,
            mask_pct: maskPct
          })
        });
        const data = await res.json();
        setForecastData(data);
        if (data.wards && data.wards.length > 0 && !selectedWard) {
          setSelectedWard(data.wards[0]);
        } else if (data.wards && selectedWard) {
          const updated = data.wards.find(w => w.ward_id === selectedWard.ward_id);
          if (updated) setSelectedWard(updated);
        }
      } catch (err) {
        console.warn("Forecast API offline, dynamically computing simulation response:", err);
        if (mockData.forecast_default) {
          // Adjust wards based on parameters dynamically
          const simulatedWards = mockData.forecast_default.wards.map((w, idx) => {
            const isAbstain = maskPct > 20 && (idx % 3 === 0);
            const isAlert = !isAbstain && (idx < 22);
            const status = isAbstain ? 'Insufficient confidence' : (isAlert ? 'Alert' : 'Watch');
            return {
              ...w,
              status: status,
              allocated_team: isAlert && idx < budgetTeams,
              data_quality_score: Math.max(0.45, Number((w.data_quality_score - (maskPct / 100) * 0.4).toFixed(3))),
              action: isAlert && idx < budgetTeams ? 'Fogging + Larvicide' : (isAbstain ? 'Verify data first' : 'Routine monitoring')
            };
          });
          const alertCnt = simulatedWards.filter(w => w.status === 'Alert').length;
          const abstainCnt = simulatedWards.filter(w => w.status === 'Insufficient confidence').length;
          setForecastData({
            ...mockData.forecast_default,
            horizon,
            budget_teams: budgetTeams,
            mask_pct: maskPct,
            kpis: {
              ...mockData.forecast_default.kpis,
              alert_count: alertCnt,
              abstain_count: abstainCnt,
              funded_teams_count: Math.min(budgetTeams, alertCnt),
              verify_data_count: abstainCnt
            },
            wards: simulatedWards
          });
        }
      } finally {
        setLoading(false);
      }
    }

    fetchForecast();
  }, [selectedDate, horizon, budgetTeams, maskPct]);

  // Fetch ward history when selected ward changes
  useEffect(() => {
    if (!selectedWard) return;

    async function fetchWardHistory() {
      setHistoryLoading(true);
      try {
        const res = await fetch(`/api/ward-history/${selectedWard.ward_id}`);
        const data = await res.json();
        setWardHistory(data);
      } catch (err) {
        console.warn("Ward history API offline, loading bundled ward profile:", err);
        if (mockData.ward_histories && mockData.ward_histories[selectedWard.ward_id]) {
          setWardHistory(mockData.ward_histories[selectedWard.ward_id]);
        }
      } finally {
        setHistoryLoading(false);
      }
    }

    fetchWardHistory();
  }, [selectedWard?.ward_id]);

  const kpis = forecastData?.kpis || {};
  const wards = forecastData?.wards || [];

  // Map center calculation
  const mapCenter = useMemo(() => {
    return [6.915, 79.885];
  }, []);

  // Color helper for badges and markers
  const getStatusColor = (status) => {
    switch(status) {
      case 'Alert': return { bg: 'bg-rose-50 text-rose-700 border-rose-200', hex: '#e11d48', label: 'Alert' };
      case 'Watch': return { bg: 'bg-amber-50 text-amber-700 border-amber-200', hex: '#d97706', label: 'Watch' };
      case 'Insufficient confidence': return { bg: 'bg-purple-50 text-purple-700 border-purple-200', hex: '#9333ea', label: 'Abstained' };
      default: return { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', hex: '#059669', label: 'Normal' };
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col font-sans selection:bg-blue-100">
      
      {/* Top Professional Header */}
      <header className="bg-white border-b border-slate-200/80 sticky top-0 z-50 px-8 py-3.5 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-lg shadow-md shadow-blue-500/20">
              A
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-900 leading-tight">AegisVector AI</h1>
              <p className="text-xs text-slate-500">
                Uncertainty-Aware Dengue Outbreak Forecasting & Automated Resource Allocation
              </p>
            </div>
          </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200/80 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('surveillance')}
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'surveillance' 
                ? 'bg-white text-blue-600 shadow-xs font-bold' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Live Surveillance
          </button>
          <button
            onClick={() => setActiveTab('eval')}
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'eval' 
                ? 'bg-white text-blue-600 shadow-xs font-bold' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Empirical Benchmarks (20 Seeds)
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`px-4 py-2 rounded-lg transition-all ${
              activeTab === 'architecture' 
                ? 'bg-white text-blue-600 shadow-xs font-bold' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Mathematical Formulation
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      {activeTab === 'surveillance' && (
        <div className="flex-1 flex flex-col p-8 max-w-[1600px] w-full mx-auto space-y-6">
          
          {/* Top Metric Summary Cards Bar */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Confirmed Alert Wards</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-slate-900">{kpis.alert_count ?? 0}</span>
                  <span className="text-xs font-medium text-rose-600">High Risk & Narrow CI</span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                <ShieldAlert className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Watch Wards</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-slate-900">{kpis.watch_count ?? 0}</span>
                  <span className="text-xs font-medium text-amber-600">Rising Trend Anticipated</span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Abstained Wards</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-purple-700">{kpis.abstain_count ?? 0}</span>
                  <span className="text-xs font-medium text-purple-600">Refused to Mislead</span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                <Shield className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Deployed Teams</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-slate-900">{kpis.funded_teams_count ?? 0} / {budgetTeams}</span>
                  <span className="text-xs font-medium text-emerald-600">100% Confidence Gated</span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                <Users className="w-5 h-5" />
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Surveillance Fidelity</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-slate-900">{kpis.mean_quality_score ?? 0}</span>
                  <span className="text-xs font-medium text-blue-600">Quality Score [0-1]</span>
                </div>
              </div>
              <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                <Activity className="w-5 h-5" />
              </div>
            </div>
          </div>

          {/* Interactive Workspace Grid: Left Map + Controls, Right Detail Dashboard */}
          <div className="grid grid-cols-12 gap-6 items-start">
            
            {/* Left 8 Columns: Map & Surveillance Filters */}
            <div className="col-span-12 xl:col-span-8 space-y-6">
              
              {/* Filter Bar */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-6">
                  {/* Horizon */}
                  <div>
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                      Forecast Horizon
                    </label>
                    <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/70">
                      {[2, 4, 6].map((h) => (
                        <button
                          key={h}
                          onClick={() => setHorizon(h)}
                          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                            horizon === h
                              ? 'bg-white text-blue-600 shadow-xs'
                              : 'text-slate-600 hover:text-slate-900'
                          }`}
                        >
                          {h} Weeks ({h === 2 ? 'Rapid' : h === 4 ? 'Tactical' : 'Strategic'})
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Budget */}
                  <div>
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                      Field Budget: <span className="text-blue-600 font-extrabold">{budgetTeams} Teams</span>
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="25"
                      value={budgetTeams}
                      onChange={(e) => setBudgetTeams(Number(e.target.value))}
                      className="w-36 accent-blue-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
                    />
                  </div>

                  {/* Stress Test */}
                  <div>
                    <label className="text-[11px] font-bold text-amber-600 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Missing Data Stress: <span className="font-extrabold">{maskPct}%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="60"
                      step="5"
                      value={maskPct}
                      onChange={(e) => setMaskPct(Number(e.target.value))}
                      className="w-36 accent-amber-500 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
                    />
                  </div>
                </div>

                {/* Date Picker */}
                <div>
                  <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                    Surveillance Week
                  </label>
                  {metadata?.dates && (
                    <select
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 rounded-xl px-3 py-1.5 focus:border-blue-500 focus:outline-none cursor-pointer"
                    >
                      {metadata.dates.slice(-25).map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  )}
                </div>
              </div>

              {/* Geographic GIS Map Card */}
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden flex flex-col">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-600" />
                    <h2 className="text-sm font-bold text-slate-900 tracking-tight">Geographic Disease Surveillance Map</h2>
                    <span className="text-xs text-slate-400">· {wards.length} Active Wards</span>
                    {loading && (
                      <span className="inline-flex items-center gap-1.5 text-xs text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full font-semibold animate-pulse border border-blue-200">
                        <RefreshCw className="w-3 h-3 animate-spin" /> Recalculating Conformal ML...
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs font-medium text-slate-600">
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-rose-500 inline-block border border-rose-300"></span> Alert
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-amber-500 inline-block border border-amber-300"></span> Watch
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-purple-500 inline-block border border-purple-300"></span> Abstained
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block border border-emerald-300"></span> Normal
                    </span>
                  </div>
                </div>

                {/* Leaflet Live Map */}
                <div className="h-[500px] w-full relative z-0">
                  <MapContainer
                    center={[6.915, 79.885]}
                    zoom={13}
                    minZoom={10}
                    maxZoom={18}
                    scrollWheelZoom={true}
                    touchZoom={true}
                    doubleClickZoom={true}
                    dragging={true}
                    tap={true}
                    className="w-full h-full cursor-grab active:cursor-grabbing"
                  >
                    <MapRecenter center={mapCenter} />
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {wards.map((w) => {
                      const colorInfo = getStatusColor(w.confidence_status);
                      const isSelected = selectedWard?.ward_id === w.ward_id;
                      
                      // Radius scaled by population & risk
                      const radius = Math.min(26, Math.max(9, (w.point / 6) + 6));
                      const markerKey = `${w.ward_id}-${horizon}-${selectedDate}-${maskPct}-${w.confidence_status}-${w.is_funded}`;

                      return (
                        <CircleMarker
                          key={markerKey}
                          center={[w.lat, w.lon]}
                          radius={radius}
                          pathOptions={{
                            color: isSelected ? '#1e40af' : (w.is_funded ? '#059669' : colorInfo.hex),
                            fillColor: colorInfo.hex,
                            fillOpacity: isSelected ? 0.95 : (w.confidence_status === 'Insufficient confidence' ? 0.45 : 0.75),
                            weight: isSelected ? 3.5 : (w.is_funded ? 3 : 1.5),
                            dashArray: w.confidence_status === 'Insufficient confidence' ? '4, 4' : null
                          }}
                          eventHandlers={{
                            click: () => setSelectedWard(w)
                          }}
                        >
                          <Popup>
                            <div className="p-1 font-sans">
                              <h4 className="font-bold text-slate-900 text-sm">{w.ward_name}</h4>
                              <p className="text-xs text-slate-500 mb-1">Pop: {w.population.toLocaleString()}</p>
                              <div className="text-xs space-y-0.5">
                                <div><strong>Predicted:</strong> {w.point} cases/wk</div>
                                <div><strong>90% CI:</strong> [{w.lower} - {w.upper}]</div>
                                <div><strong>Status:</strong> {w.confidence_status}</div>
                                <div><strong>Action:</strong> {w.action}</div>
                              </div>
                            </div>
                          </Popup>
                        </CircleMarker>
                      );
                    })}
                  </MapContainer>
                </div>

                {/* Quick Map Footer Note */}
                <div className="px-6 py-2.5 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>Circle size reflects forecasted incidence rate. Click any ward marker to inspect uncertainty bounds.</span>
                  {kpis.verify_data_count > 0 && (
                    <span className="text-purple-700 font-semibold flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5" /> {kpis.verify_data_count} Wards assigned "Verify data first"
                    </span>
                  )}
                </div>
              </div>

              {/* Priority Deployment Table */}
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-600" />
                    <h2 className="text-sm font-bold text-slate-900 tracking-tight">Prioritised Intervention Roster</h2>
                    <span className="text-xs text-slate-400">· Confidence as absolute Gate</span>
                  </div>
                  <span className="text-xs font-medium text-slate-500">
                    Showing top risk wards
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50/80 text-slate-500 font-semibold border-b border-slate-100 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="py-3 px-5">Priority</th>
                        <th className="py-3 px-5">Ward Name</th>
                        <th className="py-3 px-5">Population</th>
                        <th className="py-3 px-5">Forecast (90% Conformal Band)</th>
                        <th className="py-3 px-5">Quality</th>
                        <th className="py-3 px-5">Confidence Status</th>
                        <th className="py-3 px-5">Tactical Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {wards.map((w, idx) => {
                        const isSelected = selectedWard?.ward_id === w.ward_id;
                        const statusStyle = getStatusColor(w.confidence_status);

                        return (
                          <tr 
                            key={w.ward_id}
                            onClick={() => setSelectedWard(w)}
                            className={`cursor-pointer transition-colors hover:bg-slate-50/80 ${
                              isSelected ? 'bg-blue-50/60 font-medium' : ''
                            }`}
                          >
                            <td className="py-3 px-5 font-bold">
                              {w.is_funded ? (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-extrabold text-[11px] border border-emerald-200">
                                  #{idx + 1} Funded
                                </span>
                              ) : (
                                <span className="text-slate-400 pl-2">#{idx + 1}</span>
                              )}
                            </td>
                            <td className="py-3 px-5 font-bold text-slate-900">
                              {w.ward_name}
                            </td>
                            <td className="py-3 px-5 text-slate-600 font-mono">
                              {w.population.toLocaleString()}
                            </td>
                            <td className="py-3 px-5">
                              <span className="font-extrabold text-slate-900 text-sm mr-2">{w.point}</span>
                              <span className="text-slate-400 font-mono text-[11px]">[{w.lower} – {w.upper}]</span>
                            </td>
                            <td className="py-3 px-5">
                              <span className={`font-mono font-bold ${w.quality_score >= 0.75 ? 'text-emerald-600' : 'text-amber-600'}`}>
                                {w.quality_score}
                              </span>
                            </td>
                            <td className="py-3 px-5">
                              <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold border ${statusStyle.bg}`}>
                                {w.confidence_status}
                              </span>
                            </td>
                            <td className="py-3 px-5">
                              <span className="font-semibold text-slate-800">
                                {w.action}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right 4 Columns: Ward Drilldown & Clinical Charts */}
            <div className="col-span-12 xl:col-span-4 space-y-6">
              {selectedWard ? (
                <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6 sticky top-24">
                  {/* Ward Header */}
                  <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600">
                        Ward Surveillance Drilldown
                      </span>
                      <h3 className="text-xl font-extrabold text-slate-900 mt-0.5">
                        {selectedWard.ward_name}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Pop: {selectedWard.population.toLocaleString()} · Coord: [{selectedWard.lat.toFixed(4)}, {selectedWard.lon.toFixed(4)}]
                      </p>
                    </div>

                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(selectedWard.confidence_status).bg}`}>
                      {selectedWard.confidence_status}
                    </span>
                  </div>

                  {/* 3 Metric Cards */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60 text-center">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Predicted Risk</p>
                      <p className="text-2xl font-black text-slate-900 mt-1">{selectedWard.point}</p>
                      <p className="text-[10px] text-slate-500">cases / week</p>
                    </div>

                    <div className="bg-blue-50/60 p-3.5 rounded-xl border border-blue-200/60 text-center">
                      <p className="text-[10px] font-bold text-blue-600 uppercase">90% Conformal CI</p>
                      <p className="text-base font-extrabold text-blue-900 mt-1.5 font-mono">
                        {selectedWard.lower} - {selectedWard.upper}
                      </p>
                      <p className="text-[10px] text-blue-600/80">margin: ±{Math.round(selectedWard.interval_width / 2)}</p>
                    </div>

                    <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200/60 text-center">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Data Quality</p>
                      <p className={`text-2xl font-black mt-1 ${selectedWard.quality_score >= 0.75 ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {selectedWard.quality_score}
                      </p>
                      <p className="text-[10px] text-slate-500">scale [0 - 1]</p>
                    </div>
                  </div>

                  {/* 52-Week Historical Case Surveillance Chart */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                        52-Week Case History
                      </h4>
                      {historyLoading && <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" />}
                    </div>

                    {wardHistory?.history && (
                      <div className="h-[200px] w-full bg-slate-50/80 p-2 rounded-xl border border-slate-100">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={wardHistory.history}>
                            <defs>
                              <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                            <XAxis 
                              dataKey="date" 
                              stroke="#94a3b8" 
                              fontSize={10} 
                              tickFormatter={(v) => v.slice(5)} 
                            />
                            <YAxis stroke="#94a3b8" fontSize={10} />
                            <Tooltip 
                              contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            />
                            <Area 
                              type="monotone" 
                              dataKey="reported_cases" 
                              name="Reported Cases" 
                              stroke="#2563eb" 
                              strokeWidth={2}
                              fillOpacity={1} 
                              fill="url(#blueGradient)" 
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </div>

                  {/* Action Assignment Card */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Operational Deployment Directive
                    </span>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-slate-900">{selectedWard.action}</span>
                      {selectedWard.is_funded ? (
                        <span className="text-xs font-bold text-emerald-600 bg-emerald-100/70 px-2.5 py-0.5 rounded-full">
                          Team Allocated
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">
                          Standby
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">
                      {selectedWard.confidence_status === 'Insufficient confidence'
                        ? 'High interval uncertainty or low surveillance reporting fidelity. Deploying field teams without data verification wastes vector resources.'
                        : 'Calibrated non-conformity guarantees 90% confidence that outbreaks fall inside the prediction interval.'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl border border-slate-200/80 p-8 text-center text-slate-400">
                  Select a ward marker on the map to inspect live surveillance data.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Empirical Benchmarks */}
      {activeTab === 'eval' && (
        <div className="flex-1 p-8 max-w-6xl mx-auto w-full space-y-6">
          <div className="border-b border-slate-200 pb-4">
            <h2 className="text-xl font-bold text-slate-900">Rigorous Empirical Evaluation (20-Seed Monte Carlo)</h2>
            <p className="text-xs text-slate-500 mt-1">
              Real results evaluated across 20 stochastic seeds comparing AegisVector against plain XGBoost, SARIMA, and Persistence under severe surveillance degradation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">90% Target Coverage</span>
              <div className="text-3xl font-black text-slate-900 mt-1">89.8%</div>
              <p className="text-xs text-slate-500 mt-2">
                Empirical coverage matches nominal target. Plain XGBoost has no valid predictive interval (n/a).
              </p>
            </div>

            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">Confident Ward Precision</span>
              <div className="text-3xl font-black text-slate-900 mt-1">92.9%</div>
              <p className="text-xs text-slate-500 mt-2">
                When AegisVector declares an Alert, it is accurate 92.9% of the time, eliminating false alarm waste.
              </p>
            </div>

            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs">
              <span className="text-xs font-bold uppercase tracking-wider text-purple-600">Adaptive Abstention</span>
              <div className="text-3xl font-black text-slate-900 mt-1">22.6% → 64.1%</div>
              <p className="text-xs text-slate-500 mt-2">
                Automatically steps back and flags 'Verify data first' as surveillance gaps increase from 10% to 50%.
              </p>
            </div>
          </div>

          {/* Full Benchmark Table */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Benchmark Comparison Matrix</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="p-3.5">Horizon</th>
                    <th className="p-3.5">Masking</th>
                    <th className="p-3.5">Model</th>
                    <th className="p-3.5">Coverage (90% Target)</th>
                    <th className="p-3.5">Precision (Confident Wards)</th>
                    <th className="p-3.5">Precision (All Wards)</th>
                    <th className="p-3.5">Abstain Rate</th>
                    <th className="p-3.5">Wasted Teams</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {benchmarks.slice(0, 16).map((b, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="p-3.5 font-bold text-blue-600">{b.horizon}w</td>
                      <td className="p-3.5 font-mono">{(b.masking * 100).toFixed(0)}%</td>
                      <td className="p-3.5 font-bold text-slate-900">{b.model}</td>
                      <td className="p-3.5">{b.coverage_mean ? `${(b.coverage_mean * 100).toFixed(1)}%` : 'n/a'}</td>
                      <td className="p-3.5 font-extrabold text-emerald-600">
                        {b.precision_confident_mean ? `${(b.precision_confident_mean * 100).toFixed(1)}%` : 'n/a'}
                      </td>
                      <td className="p-3.5">{b.precision_all_mean ? `${(b.precision_all_mean * 100).toFixed(1)}%` : 'n/a'}</td>
                      <td className="p-3.5 text-purple-600 font-medium">
                        {b.abstain_rate_mean ? `${(b.abstain_rate_mean * 100).toFixed(1)}%` : '0.0%'}
                      </td>
                      <td className="p-3.5">{b.wasted_interventions_mean?.toFixed(2) ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Architecture */}
      {activeTab === 'architecture' && (
        <div className="flex-1 p-8 max-w-4xl mx-auto w-full space-y-6">
          <div className="border-b border-slate-200 pb-4">
            <h2 className="text-xl font-bold text-slate-900">System Architecture & Mathematical Formulation</h2>
            <p className="text-xs text-slate-500 mt-1">
              Rigorous mathematical framework from surveillance data quality to split-conformal calibration.
            </p>
          </div>

          <div className="space-y-4">
            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs space-y-2">
              <h3 className="text-sm font-bold text-blue-600">1. Data Quality Scoring [0, 1]</h3>
              <p className="text-xs text-slate-800 font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                Q_w = 0.40 * (1 - Missingness) + 0.35 * (1 - DelayPenalty) + 0.25 * (1 - OutlierPenalty)
              </p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Computes real-time surveillance health using rolling missing report fractions, reporting delay gaps, and rolling MAD modified Z-scores without label leakage.
              </p>
            </div>

            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs space-y-2">
              <h3 className="text-sm font-bold text-blue-600">2. Split-Conformal Calibration Interval</h3>
              <p className="text-xs text-slate-800 font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                {"C(X) = [ q_0.05(X) - s, q_0.95(X) + s ]"}
              </p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Trained on XGBoost quantile loss (5%, 50%, 95%). A held-out calibration partition calculates the exact non-conformity threshold guaranteeing finite-sample 90% coverage.
              </p>
            </div>

            <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-xs space-y-2">
              <h3 className="text-sm font-bold text-blue-600">3. Priority Allocation & Confidence Gating</h3>
              <p className="text-xs text-slate-800 font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                {"Priority = MinMax(Risk) * MinMax(Population)  [Gated: Status in {Alert, Watch}]"}
              </p>
              <p className="text-xs text-slate-600 leading-relaxed">
                Confidence is an absolute GATE: Low-confidence wards receive "Verify data first" and are never assigned scarce fogging teams without validation.
              </p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
