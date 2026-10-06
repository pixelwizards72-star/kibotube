import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  CalendarDays, MessageSquare, BarChart3, Settings, Bell, Search,
  PlusCircle, Video, Image as ImageIcon, Link as LinkIcon, Key,
  MessageCircle, Wand2, X, Zap, CalendarCheck, Radio, Server, Activity, Edit3, ShieldCheck
} from 'lucide-react';
import { format, addDays, subDays, isSameDay } from 'date-fns';

const api = axios.create({ 
  baseURL: 'https://kibotube-api-preview.loca.lt',
  headers: { 'Bypass-Tunnel-Reminder': 'true' }
});

const PLATFORMS = ['meta', 'x', 'instagram', 'tiktok'];
const FOCUS_AREAS = [
  'Medicine', 'Football', 'Agriculture', 'News', 'Technology', 
  'Finance', 'Entertainment', 'Science', 'Politics', 'Lifestyle'
];

export default function App() {
  const [activeTab, setActiveTab] = useState('connections'); // Default to connections to show off the new feature
  const [posts, setPosts] = useState([]);
  const [inbox, setInbox] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [config, setConfig] = useState(null);
  
  const [stats, setStats] = useState(null);
  const [insightPlatform, setInsightPlatform] = useState('all');
  const [inboxPlatform, setInboxPlatform] = useState('all');
  
  const [editingPost, setEditingPost] = useState(null);

  const [selectedEngine, setSelectedEngine] = useState(1);

  const [engine1Post, setEngine1Post] = useState({ 
    platform: 'meta', content_type: 'post', focus_area: '', description: '', tone: 'Professional', content: ''
  });

  const [engine2Post, setEngine2Post] = useState({ 
    platform: 'x', content_type: 'post', focus_area: 'Technology', description: '', tone: 'Urgent, Breaking News', rss_url: '', cadence: 1
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");

  // OAuth Simulation States
  const [authPopup, setAuthPopup] = useState(null); // 'meta', 'x', 'tiktok'
  const [fbPagesModal, setFbPagesModal] = useState(null);

  useEffect(() => {
    fetchData();
  }, [insightPlatform, inboxPlatform]);

  const fetchData = async () => {
    try {
      const [postsRes, inboxRes, profRes, confRes, statRes] = await Promise.all([
        api.get('/posts/'),
        api.get(`/inbox/?platform=${inboxPlatform}`),
        api.get('/profiles/'),
        api.get('/agent-config/'),
        api.get(`/stats/?platform=${insightPlatform}`)
      ]);
      setPosts(postsRes.data);
      setInbox(inboxRes.data);
      setProfiles(profRes.data);
      setConfig(confRes.data);
      setStats(statRes.data);
    } catch (error) {
      console.error("API Error", error);
    }
  };

  const handleOAuthConnect = async (platform) => {
    // 1. Show simulated popup
    setAuthPopup(platform);
    
    // 2. Simulate user going through OAuth flow on the platform's site
    setTimeout(async () => {
      try {
        // 3. Callback hits our backend to exchange code for tokens
        await api.post(`/auth/${platform}/callback`, { code: "simulated_oauth_code_123" });
        setAuthPopup(null);
        
        // 4. If Facebook, fetch pages and show selector modal
        if (platform === 'meta') {
          const pagesRes = await api.get('/auth/facebook/pages');
          setFbPagesModal(pagesRes.data);
        } else {
          // Normal success for others
          alert(`Successfully connected ${platform} via OAuth 2.0!`);
          fetchData();
        }
      } catch (err) {
        alert("OAuth Connection Failed");
        setAuthPopup(null);
      }
    }, 2000);
  };

  const handleSelectFbPage = async (page) => {
    try {
      await api.post('/auth/facebook/select-page', { page_id: page.id, page_name: page.name });
      setFbPagesModal(null);
      alert(`Successfully linked Facebook Page: ${page.name}`);
      fetchData();
    } catch (err) {
      alert("Failed to select page");
    }
  };

  const handleConfigSave = async (e) => {
    e.preventDefault();
    await api.put('/agent-config/', config);
    alert('Settings Saved!');
  };

  const handleAIGenerateSingle = async () => {
    if (!engine1Post.focus_area || !engine1Post.description) {
      alert("Please fill in Focus Area and Instructions."); return;
    }
    // Check if account connected
    const prof = profiles.find(p => p.platform === engine1Post.platform);
    if (!prof || !prof.is_connected) {
      alert(`Please connect your ${engine1Post.platform} account first in the Connections tab.`);
      return;
    }

    setLoadingMsg("Generating single post with AI Image..."); setIsGenerating(true);
    try {
      const res = await api.post('/ai/generate-draft', {
        focus_area: engine1Post.focus_area, description: engine1Post.description, tone: engine1Post.tone,
        platform: engine1Post.platform, content_type: engine1Post.content_type
      });
      setEngine1Post({ ...engine1Post, content: res.data.content, image_url: res.data.image_url });
    } catch (error) { alert("Error generating content."); }
    setIsGenerating(false);
  };

  const handleAIGenerateBulk = async (days, engine) => {
    let payload = {};
    if (engine === 1) {
      if (!engine1Post.focus_area || !engine1Post.description) { alert("Fill all instructions."); return; }
      payload = { ...engine1Post, days, source_engine: "engine_1", posts_per_day: 1 };
    } else {
      if (!engine2Post.rss_url || !engine2Post.description) { alert("RSS URL and Instructions are required for Engine 2."); return; }
      payload = { ...engine2Post, days, source_engine: "engine_2", posts_per_day: engine2Post.cadence };
    }

    const prof = profiles.find(p => p.platform === payload.platform);
    if (!prof || !prof.is_connected) {
      alert(`Error: You cannot schedule to ${payload.platform}. Please connect your account first in the Connections tab.`);
      return;
    }

    setLoadingMsg(`AI is generating texts and images for ${days * payload.posts_per_day} posts using Engine ${engine}...`);
    setIsGenerating(true);
    try {
      const res = await api.post('/ai/generate-bulk', payload);
      alert(`Success! Scheduled ${res.data.scheduled_count} posts.`);
      fetchData();
    } catch (error) { alert("Error generating bulk content."); }
    setIsGenerating(false);
  };

  const handleUpdatePost = async (e) => {
    e.preventDefault();
    await api.put(`/posts/${editingPost.id}`, { content: editingPost.content });
    alert('Post Updated!');
    setEditingPost(null);
    fetchData();
  };

  const today = new Date();
  const calendarDays = Array.from({ length: 30 }).map((_, i) => addDays(subDays(today, 15), i));

  const eng1Queue = posts.filter(p => p.source_engine === 'engine_1' && !p.is_published).sort((a,b) => new Date(a.scheduled_time) - new Date(b.scheduled_time));
  const eng2Queue = posts.filter(p => p.source_engine === 'engine_2' && !p.is_published).sort((a,b) => new Date(a.scheduled_time) - new Date(b.scheduled_time));

  const eng2Posts = posts.filter(p => p.source_engine === 'engine_2');
  const eng2Total = eng2Posts.length;
  const eng2Yesterday = eng2Posts.filter(p => isSameDay(new Date(p.scheduled_time), subDays(today, 1))).length;
  const eng2Today = eng2Posts.filter(p => isSameDay(new Date(p.scheduled_time), today)).length;
  const eng2Impressions = eng2Posts.reduce((acc, curr) => acc + curr.impressions, 0);

  const PreviewQueue = ({ queue }) => {
    if (queue.length === 0) return <div className="text-muted p-4">No upcoming posts scheduled for this engine.</div>;
    const upNext = queue[0];
    const futureQueue = queue.slice(1, 4); // show next 3
    
    return (
      <div className="mt-8">
        <h2 className="mb-4 text-primary"><CalendarCheck size={20} className="inline-icon" /> Up Next Spotlight</h2>
        <div className="glass-card mb-8" style={{ border: '1px solid var(--primary-color)' }}>
          <div className="flex gap-6">
            <div className="flex-1">
              <div className="flex-between mb-4">
                <span className={`platform-badge bg-${upNext.platform}`}>{upNext.platform}</span>
                <span className="text-sm text-muted">Scheduled: {format(new Date(upNext.scheduled_time), 'MMM d, yyyy h:mm a')}</span>
              </div>
              <p className="whitespace-pre-wrap text-sm mb-4" style={{lineHeight: '1.6'}}>{upNext.content}</p>
              <button className="btn btn-secondary" onClick={() => setEditingPost(upNext)}><Edit3 size={16}/> Edit Next Post</button>
            </div>
            {upNext.image_url && (
              <div className="flex-1" style={{borderRadius: '8px', overflow: 'hidden'}}>
                <img src={upNext.image_url} alt="AI Generated Preview" style={{width: '100%', height: '250px', objectFit: 'cover'}} />
                <div className="text-xs text-muted text-center mt-2">AI-Generated Image Preview</div>
              </div>
            )}
          </div>
        </div>

        {futureQueue.length > 0 && (
          <>
            <h3 className="mb-4">Future Queue</h3>
            <div className="flex gap-4 overflow-x-auto pb-4">
              {futureQueue.map(p => (
                <div key={p.id} className="glass-card flex-none" style={{width: '300px', cursor: 'pointer'}} onClick={() => setEditingPost(p)}>
                  {p.image_url && <img src={p.image_url} style={{width: '100%', height: '120px', objectFit: 'cover', borderRadius: '6px', marginBottom: '12px'}} />}
                  <span className={`platform-badge bg-${p.platform} text-xs mb-2 block w-fit`}>{p.platform}</span>
                  <div className="text-xs text-muted mb-2">{format(new Date(p.scheduled_time), 'MMM d, h:mm a')}</div>
                  <p className="text-sm truncate text-muted">{p.content}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      {isGenerating && (
        <div className="modal-overlay" style={{zIndex: 9999}}>
          <div className="glass-card text-center p-8" style={{border: '1px solid var(--primary-color)'}}>
            <Wand2 size={48} className="mx-auto mb-4" color="var(--primary-color)" />
            <h3>{loadingMsg}</h3>
          </div>
        </div>
      )}

      {/* Simulated OAuth Popup */}
      {authPopup && (
        <div className="modal-overlay" style={{zIndex: 9999}}>
          <div className="glass-card text-center p-8" style={{width: '400px', background: '#fff', color: '#000'}}>
            <ShieldCheck size={48} className="mx-auto mb-4 text-blue-500" />
            <h2 style={{color: '#000'}}>Redirecting to {authPopup.toUpperCase()}...</h2>
            <p className="text-gray-600 mb-6">Securely connecting your account via official OAuth 2.0.</p>
            <div className="animate-pulse flex justify-center">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          </div>
        </div>
      )}

      {/* Facebook Page Selector Modal */}
      {fbPagesModal && (
        <div className="modal-overlay" style={{zIndex: 9999}}>
          <div className="glass-card p-8" style={{width: '500px'}}>
            <h2 className="mb-2"><ShieldCheck size={24} className="inline-icon text-blue-500" /> Facebook Connected!</h2>
            <p className="text-muted mb-6">Please select which Facebook Page you want KiboTube to manage.</p>
            
            <div className="flex flex-col gap-3">
              {fbPagesModal.map(page => (
                <button 
                  key={page.id} 
                  className="btn btn-secondary w-full text-left flex-between p-4"
                  onClick={() => handleSelectFbPage(page)}
                  style={{border: '1px solid var(--suite-border)'}}
                >
                  <div>
                    <div className="font-bold">{page.name}</div>
                    <div className="text-xs text-muted mt-1">{page.category} (ID: {page.id})</div>
                  </div>
                  <span className="text-primary">&rarr; Select</span>
                </button>
              ))}
            </div>
            <button className="btn mt-6 w-full text-center" onClick={() => setFbPagesModal(null)}>Cancel</button>
          </div>
        </div>
      )}

      <aside className="suite-sidebar">
        <div className="suite-header">
          <div className="suite-brand">KiboTube Suite</div>
          <select className="workspace-selector">
            <option>My Business Workspace</option>
          </select>
        </div>
        <nav className="suite-nav">
          <NavItem icon={<Bell size={20} />} label="Notifications" badge={3} onClick={() => setActiveTab('notifications')} active={activeTab === 'notifications'} />
          <NavItem icon={<CalendarDays size={20} />} label="Planner" onClick={() => setActiveTab('planner')} active={activeTab === 'planner'} />
          <NavItem icon={<MessageSquare size={20} />} label="Inbox" badge={inbox.filter(m => !m.is_read).length} onClick={() => setActiveTab('inbox')} active={activeTab === 'inbox'} />
          <NavItem icon={<MessageCircle size={20} />} label="Comments" onClick={() => setActiveTab('comments')} active={activeTab === 'comments'} />
          <NavItem icon={<BarChart3 size={20} />} label="Insights" onClick={() => setActiveTab('insights')} active={activeTab === 'insights'} />
          <hr className="nav-divider" />
          <NavItem icon={<LinkIcon size={20} />} label="Connections" onClick={() => setActiveTab('connections')} active={activeTab === 'connections'} />
          <NavItem icon={<Settings size={20} />} label="Settings & AI" onClick={() => setActiveTab('settings')} active={activeTab === 'settings'} />
        </nav>
      </aside>

      <main className="suite-main">
        <header className="suite-topbar">
          <div className="topbar-search"><Search size={18} className="search-icon" /><input type="text" placeholder="Search..." /></div>
          <div className="topbar-profiles">
            {profiles.filter(p => p.is_connected && PLATFORMS.includes(p.platform)).map(p => (
              <div key={p.id} className="profile-chip">
                <div className={`platform-dot bg-${p.platform}`}></div><span>{p.followers.toLocaleString()} Followers</span>
              </div>
            ))}
          </div>
        </header>

        <div className="suite-content-area relative">
          
          {activeTab === 'connections' && (
            <div className="view-connections fade-in max-w-4xl mx-auto">
              <div className="text-center mb-12">
                <h1>Official Integrations</h1>
                <p className="text-muted">Connect your social media accounts via secure OAuth 2.0 to safely automate posting without risking platform bans.</p>
              </div>
              <div className="connections-grid">
                {PLATFORMS.map(plat => {
                  const profile = profiles.find(p => p.platform === plat);
                  const isConnected = profile?.is_connected;
                  
                  return (
                    <div key={plat} className="connection-card glass-card relative" style={{border: isConnected ? '1px solid var(--primary-color)' : ''}}>
                      {isConnected && <div className="absolute top-4 right-4"><ShieldCheck size={20} color="var(--primary-color)" /></div>}
                      <div className="connection-header">
                        <div className={`platform-logo bg-${plat}`}></div>
                        <h3 style={{textTransform:'capitalize', margin:0}}>{plat === 'meta' ? 'Facebook/Meta' : plat}</h3>
                      </div>
                      
                      {isConnected ? (
                        <div className="connection-stats mt-4">
                          <p className="text-sm text-muted mb-1">Connected as:</p>
                          <p className="font-bold text-lg mb-2">@{profile.username || profile.page_name}</p>
                          {plat === 'meta' && <p className="text-xs text-muted mb-4">Managing Page ID: {profile.page_id}</p>}
                          
                          <div className="flex-between text-xs text-muted mb-6">
                            <span>Status: <span style={{color: '#22c55e'}}>Active</span></span>
                            <span>Token Expires: 60 Days</span>
                          </div>
                          <button className="btn btn-secondary w-full text-center" onClick={() => alert("Manage connection via OAuth Portal...")}>Manage Connection</button>
                        </div>
                      ) : (
                        <div className="connection-action mt-6">
                          <p className="text-xs text-muted mb-4 text-center">Requires official developer app authorization.</p>
                          <button className="btn btn-primary w-full flex justify-center gap-2" onClick={() => handleOAuthConnect(plat)}>
                            <LinkIcon size={16} /> Connect Account
                          </button>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {activeTab === 'planner' && (
            <div className="view-planner fade-in">
              <div className="view-header">
                <h2>30-Day Planner</h2>
                <button className="btn btn-primary" onClick={() => setActiveTab('content_engines')}><Server size={18} /> Content Engines</button>
              </div>
              
              <div className="calendar-grid">
                {calendarDays.map((date, idx) => {
                  const dayPosts = posts.filter(p => isSameDay(new Date(p.scheduled_time), date));
                  const isToday = isSameDay(date, today);
                  return (
                    <div key={idx} className={`calendar-cell ${isToday ? 'is-today' : ''}`}>
                      <div className="cell-date">{format(date, 'MMM d')}</div>
                      <div className="cell-platforms">
                        {PLATFORMS.map(plat => {
                          const platPost = dayPosts.find(p => p.platform === plat);
                          return (
                            <div key={plat} className={`plat-row ${platPost ? 'clickable' : ''}`} onClick={() => platPost && setEditingPost(platPost)}>
                              <span className="plat-name">{plat}</span>
                              {platPost ? (platPost.error_message ? <span className="status-err">❌</span> : <span className="status-ok">✅</span>) : (<span className="status-none">➖</span>)}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {activeTab === 'content_engines' && (
            <div className="view-engines fade-in" style={{maxWidth: '1200px', margin: '0 auto'}}>
              <h2 className="mb-4">Select Content Engine</h2>
              
              <div className="flex gap-4 mb-8">
                {[1, 2, 3, 4].map(engineNum => (
                  <button 
                    key={engineNum}
                    className={`btn flex-1 ${selectedEngine === engineNum ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setSelectedEngine(engineNum)}
                    style={{padding: '1rem', flexDirection: 'column', height: '100px'}}
                  >
                    {engineNum === 1 && <><Wand2 className="mb-2"/>Engine 1: Standard AI</>}
                    {engineNum === 2 && <><Zap className="mb-2"/>Engine 2: RSS Aggregator</>}
                    {engineNum === 3 && <><Server className="mb-2"/>Engine 3: Locked</>}
                    {engineNum === 4 && <><Server className="mb-2"/>Engine 4: Locked</>}
                  </button>
                ))}
              </div>

              {selectedEngine === 1 && (
                <div className="engine-panel fade-in">
                  <div className="flex gap-4">
                    <div className="glass-card flex-1">
                      <h3 className="mb-4 text-primary">Engine 1: Standard Broad Content</h3>
                      <label>Platform</label>
                      <select className="input-field" value={engine1Post.platform} onChange={e => setEngine1Post({...engine1Post, platform: e.target.value})}>
                        {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                      <label>Format</label>
                      <select className="input-field" value={engine1Post.content_type} onChange={e => setEngine1Post({...engine1Post, content_type: e.target.value})}>
                        <option value="post">Standard Post</option><option value="reel">Reel / Video</option><option value="story">Story</option>
                      </select>
                      <label>Focus Area (Broad)</label>
                      <input className="input-field" type="text" placeholder="Type any topic..." value={engine1Post.focus_area} onChange={e => setEngine1Post({...engine1Post, focus_area: e.target.value})} />
                      <label>Tone & Voice</label>
                      <input className="input-field" type="text" value={engine1Post.tone} onChange={e => setEngine1Post({...engine1Post, tone: e.target.value})} />
                      <label>Detailed Instructions</label>
                      <textarea className="input-field h-32" value={engine1Post.description} onChange={e => setEngine1Post({...engine1Post, description: e.target.value})} />
                    </div>
                    
                    <div className="glass-card flex-1">
                      <h3 className="mb-4">Standard Generation</h3>
                      <button className="btn btn-secondary w-full mb-4" onClick={handleAIGenerateSingle}>Generate Single Post</button>
                      
                      {engine1Post.image_url && (
                        <div className="mb-4">
                          <img src={engine1Post.image_url} style={{width:'100%', height:'150px', objectFit:'cover', borderRadius:'8px'}}/>
                        </div>
                      )}
                      <textarea className="input-field h-32" value={engine1Post.content} onChange={e => setEngine1Post({...engine1Post, content: e.target.value})} placeholder="Single post draft..." />
                      
                      <hr style={{borderColor: 'var(--suite-border)', margin: '1.5rem 0'}}/>
                      <h3 className="mb-2">Bulk Standard Campaign (1x per day)</h3>
                      <button className="btn btn-primary w-full mb-2" onClick={() => handleAIGenerateBulk(30, 1)}>Generate & Schedule 30 Days</button>
                      <button className="btn btn-secondary w-full" onClick={() => handleAIGenerateBulk(60, 1)}>Generate & Schedule 60 Days</button>
                    </div>
                  </div>
                  <hr style={{borderColor: 'var(--suite-border)', margin: '2rem 0'}}/>
                  <PreviewQueue queue={eng1Queue} />
                </div>
              )}

              {selectedEngine === 2 && (
                <div className="engine-panel fade-in">
                  <div className="flex gap-4">
                    <div className="glass-card flex-1">
                      <h3 className="mb-4" style={{color: '#00f2fe'}}>Engine 2: RSS News Aggregator</h3>
                      <label>Platform</label>
                      <select className="input-field" value={engine2Post.platform} onChange={e => setEngine2Post({...engine2Post, platform: e.target.value})}>
                        {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                      
                      <label>Restricted Focus Area</label>
                      <select className="input-field" value={engine2Post.focus_area} onChange={e => setEngine2Post({...engine2Post, focus_area: e.target.value})}>
                        {FOCUS_AREAS.map(fa => <option key={fa} value={fa}>{fa}</option>)}
                      </select>

                      <label>RSS Feed URL (Required)</label>
                      <input className="input-field" type="url" placeholder="https://news.yahoo.com/rss/" value={engine2Post.rss_url} onChange={e => setEngine2Post({...engine2Post, rss_url: e.target.value})} />
                      
                      <label>Tone & Voice</label>
                      <input className="input-field" type="text" value={engine2Post.tone} onChange={e => setEngine2Post({...engine2Post, tone: e.target.value})} />
                      
                      <label>Rewrite Instructions</label>
                      <textarea className="input-field h-32" placeholder="How should the AI rewrite the news?" value={engine2Post.description} onChange={e => setEngine2Post({...engine2Post, description: e.target.value})} />
                    </div>
                    
                    <div className="flex-1 flex flex-col gap-4">
                      <div className="glass-card" style={{border: '1px solid #00f2fe'}}>
                        <h3 className="mb-4">Advanced RSS Cadence Generation</h3>
                        <label>Posts per Day</label>
                        <select className="input-field" value={engine2Post.cadence} onChange={e => setEngine2Post({...engine2Post, cadence: parseInt(e.target.value)})}>
                          <option value={1}>1x a Day (Every 24 hrs)</option>
                          <option value={2}>2x a Day (Every 12 hrs)</option>
                          <option value={3}>3x a Day (Every 8 hrs)</option>
                        </select>
                        
                        <button className="btn btn-primary w-full mb-2" onClick={() => handleAIGenerateBulk(30, 2)}>
                          Scrape & Schedule Next 30 Days ({30 * engine2Post.cadence} posts)
                        </button>
                        <button className="btn btn-secondary w-full" onClick={() => handleAIGenerateBulk(60, 2)}>
                          Scrape & Schedule Next 60 Days ({60 * engine2Post.cadence} posts)
                        </button>
                      </div>

                      <div className="glass-card">
                        <h3 className="mb-4"><Activity size={18} className="inline-icon"/> Engine 2 Metrics</h3>
                        <div className="flex gap-4 text-center">
                          <div className="flex-1 p-4 bg-black rounded border border-gray-800">
                            <div className="text-2xl font-bold text-white">{eng2Total}</div>
                            <div className="text-xs text-muted uppercase">Total Posts</div>
                          </div>
                          <div className="flex-1 p-4 bg-black rounded border border-gray-800">
                            <div className="text-2xl font-bold text-white">{eng2Today}</div>
                            <div className="text-xs text-muted uppercase">Today</div>
                          </div>
                          <div className="flex-1 p-4 bg-black rounded border border-gray-800">
                            <div className="text-2xl font-bold text-white">{eng2Yesterday}</div>
                            <div className="text-xs text-muted uppercase">Yesterday</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <hr style={{borderColor: 'var(--suite-border)', margin: '2rem 0'}}/>
                  <PreviewQueue queue={eng2Queue} />
                </div>
              )}

              {(selectedEngine === 3 || selectedEngine === 4) && (
                <div className="glass-card text-center p-12">
                  <Server size={48} className="mx-auto mb-4 text-muted" />
                  <h3 className="text-muted">Engine {selectedEngine} is offline</h3>
                  <p className="text-muted">Awaiting further configuration instructions...</p>
                </div>
              )}
            </div>
          )}

          {editingPost && (
            <div className="modal-overlay">
              <div className="glass-card modal-content" style={{maxWidth: '600px'}}>
                <div className="flex-between mb-4">
                  <h3 className="m-0">Edit Post Queue</h3>
                  <X className="cursor-pointer" onClick={() => setEditingPost(null)} />
                </div>
                <form onSubmit={handleUpdatePost}>
                  {editingPost.image_url && (
                     <img src={editingPost.image_url} alt="AI Generated Preview" style={{width: '100%', height: '200px', objectFit: 'cover', borderRadius: '8px', marginBottom: '16px'}} />
                  )}
                  <textarea 
                    className="input-field h-32" 
                    value={editingPost.content}
                    onChange={(e) => setEditingPost({...editingPost, content: e.target.value})}
                  />
                  <div className="flex gap-4 mt-4">
                    <button type="submit" className="btn btn-primary w-full">Save Changes</button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {activeTab === 'inbox' && (
            <div className="view-inbox fade-in">
              <div className="flex-between mb-4">
                <h2>Unified Inbox</h2>
                <div className="platform-tabs">
                  {['all', ...PLATFORMS].map(plat => (
                    <button key={plat} className={`plat-tab ${inboxPlatform === plat ? 'active' : ''}`} onClick={() => setInboxPlatform(plat)}>{plat}</button>
                  ))}
                </div>
              </div>
              <div className="inbox-layout">
                <div className="inbox-list">
                  {inbox.map(msg => (
                    <div key={msg.id} className={`inbox-item ${!msg.is_read ? 'unread' : ''}`}>
                      <div className="inbox-item-header">
                        <span className={`platform-badge bg-${msg.platform}`}>{msg.platform}</span>
                        <span className="inbox-time">{format(new Date(msg.timestamp), 'MMM d, h:mm a')}</span>
                      </div>
                      <div className="inbox-sender">@{msg.sender_handle}</div>
                      <div className="inbox-excerpt">{msg.content}</div>
                    </div>
                  ))}
                </div>
                <div className="inbox-detail">
                  <div className="detail-placeholder">
                    <MessageSquare size={48} className="text-muted mb-4 mx-auto" />
                    <h3>Select a message to read</h3>
                    <p className="text-muted">Gemini Auto-Responder is active and monitoring.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'insights' && stats && (
            <div className="view-insights fade-in">
              <div className="flex-between mb-4">
                <h2>Global Insights</h2>
                <select className="input-field" style={{width: '200px', margin: 0}} value={insightPlatform} onChange={e => setInsightPlatform(e.target.value)}>
                  <option value="all">All Platforms</option>
                  {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="stat-grid">
                <div className="stat-box glass-card"><div className="stat-value">{stats.total_impressions.toLocaleString()}</div><div className="stat-label">Impressions</div></div>
                <div className="stat-box glass-card"><div className="stat-value">{stats.total_likes.toLocaleString()}</div><div className="stat-label">Likes</div></div>
                <div className="stat-box glass-card"><div className="stat-value">{stats.total_shares.toLocaleString()}</div><div className="stat-label">Shares</div></div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && config && (
            <div className="view-settings fade-in">
              <h2>Settings & AI Configuration</h2>
              <div className="settings-layout">
                <form onSubmit={handleConfigSave} className="flex gap-4">
                  <div className="glass-card flex-1">
                    <h3><Key size={18} className="inline-icon" /> Gemini API Authentication</h3>
                    <p className="text-muted text-sm mb-4">Input your API key to activate true autonomous capabilities.</p>
                    <input type="password" className="input-field" placeholder="AIzaSy..." value={config.gemini_api_key} onChange={(e) => setConfig({...config, gemini_api_key: e.target.value})} />
                    
                    <h3 className="mt-6">Business Persona</h3>
                    <label>Tone of Voice</label>
                    <input type="text" className="input-field" value={config.tone_of_voice} onChange={e => setConfig({...config, tone_of_voice: e.target.value})} />
                  </div>

                  <div className="glass-card flex-1">
                    <h3 style={{color: 'var(--primary-color)'}}><Radio size={18} className="inline-icon" /> Autonomous News Engine</h3>
                    <p className="text-muted text-sm mb-4">When enabled, the AI runs perpetually every 2 hours, scraping the RSS feed below, rewriting the top article, and publishing it to your social media.</p>
                    
                    <label className="flex gap-2 items-center mb-4">
                      <input type="checkbox" checked={config.news_engine_enabled} onChange={e => setConfig({...config, news_engine_enabled: e.target.checked})} style={{width: '20px', height: '20px'}} />
                      Enable 2-Hour News Auto-Pilot
                    </label>

                    <label>News Source RSS URL</label>
                    <input type="url" className="input-field" placeholder="https://news.yahoo.com/rss/" value={config.news_rss_url || ''} onChange={e => setConfig({...config, news_rss_url: e.target.value})} />

                    <button type="submit" className="btn btn-primary mt-4 w-full">Save Configuration</button>
                  </div>
                </form>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, badge, active, onClick }) {
  return (
    <div className={`suite-nav-item ${active ? 'active' : ''}`} onClick={onClick}>
      <div className="nav-item-icon">{icon}</div>
      <div className="nav-item-label">{label}</div>
      {badge > 0 && <div className="nav-item-badge">{badge}</div>}
    </div>
  );
}
