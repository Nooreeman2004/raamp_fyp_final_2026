import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import raampIcon from "@/assets/raamp-icon-transparent.png";
import { Facebook, Instagram, Map, ArrowLeft, ArrowRight } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { apiClient } from "@/services/api";
import MapsConnectModal from '@/components/MapsConnectModal';
import ProgressIndicator from "@/components/ProgressIndicator";
import Celebration from "@/components/Celebration";
import Breadcrumbs from "@/components/Breadcrumbs";


const Onboarding = () => {
  const navigate = useNavigate();
  const [connected, setConnected] = useState({ facebook: false, instagram: false, google: false });
  const [loadingConnections, setLoadingConnections] = useState(false);
  const [pagesModalOpen, setPagesModalOpen] = useState(false);
  const [pagesList, setPagesList] = useState<any[]>([]);
  const [fbScopes, setFbScopes] = useState<string[]>([]);
  const [mapsModalOpen, setMapsModalOpen] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [linkHelpOpen, setLinkHelpOpen] = useState(false);
  // Instagram will open a backend-hosted popup to list pages and link IG

  const useMock = import.meta.env.VITE_USE_MOCK_API === 'true';

  // Calculate onboarding progress
  const onboardingSteps = [
    { id: 'profile', label: 'Profile', description: 'Personal Details' },
    { id: 'facebook', label: 'Facebook', description: 'Connect Account' },
    { id: 'instagram', label: 'Instagram', description: 'Connect Account' },
    { id: 'google', label: 'Google Maps', description: 'Connect Location' },
  ];

  const getCurrentStep = () => {
    if (!connected.facebook && !connected.instagram && !connected.google) return 1;
    if (connected.facebook && !connected.instagram && !connected.google) return 2;
    if (connected.facebook && connected.instagram && !connected.google) return 3;
    if (connected.facebook && connected.instagram && connected.google) return 4;
    return 1;
  };

  const completedSteps = [];
  if (connected.facebook) completedSteps.push(1);
  if (connected.instagram) completedSteps.push(2);
  if (connected.google) completedSteps.push(3);

  const fetchConnections = async () => {
      setLoadingConnections(true);
    try {
        if (useMock) {
          // in mock mode, preserve previous state
          return;
        }

        // Use the consolidated onboarding status endpoint
        try {
          const s: any = await apiClient.get('/profile/onboarding/status');
          setConnected({ facebook: !!s.facebook_connected, instagram: !!s.instagram_connected, google: !!s.google_maps_connected });
          // fetch granted FB scopes for debugging/display
          if (s.facebook_connected) {
            try {
              const g: any = await apiClient.get('/profile/connections/facebook/granted-scopes');
              setFbScopes(g.granted_scopes || []);
            } catch (e) {
              setFbScopes([]);
            }
          } else {
            setFbScopes([]);
          }
        } catch (err) {
          // fallback to older endpoints if status endpoint unavailable
          const [fb, ig, g] = await Promise.allSettled([
            apiClient.get('/profile/connections/facebook'),
            apiClient.get('/profile/connections/instagram'),
            apiClient.get('/profile/connections/google-business'),
          ]);
          setConnected({
            facebook: fb.status === 'fulfilled' && !!(fb as any).value?.connected,
            instagram: ig.status === 'fulfilled' && !!(ig as any).value?.connected,
            google: g.status === 'fulfilled' && !!(g as any).value?.connected,
          });
          // fetch granted scopes when facebook connected
          try {
            if (fb.status === 'fulfilled' && (fb as any).value?.connected) {
              const g: any = await apiClient.get('/profile/connections/facebook/granted-scopes');
              setFbScopes(g.granted_scopes || []);
            } else {
              setFbScopes([]);
            }
          } catch (e) {
            setFbScopes([]);
          }
        }
    } catch (e) {
      // ignore
    } finally {
      setLoadingConnections(false);
    }
  };

  useEffect(() => {
    fetchConnections();
    const id = setInterval(fetchConnections, 5000);
    return () => clearInterval(id);
  }, []);

  // Show celebration when all connections are complete
  useEffect(() => {
    if (connected.facebook && connected.instagram && connected.google && !showCelebration) {
      setShowCelebration(true);
    }
  }, [connected, showCelebration]);

  const openAuthWindowAndPoll = (url: string, provider: string, onSuccess?: () => Promise<void> | void) => {
    if (provider === 'google') {
      if (useMock) {
        setTimeout(() => {
          setConnected((s) => ({ ...s, google: true }));
          toast({ title: `google connected (mock)` });
        }, 600);
        return;
      }

      // Open the modal-based search/confirm/connect flow
      setMapsModalOpen(true);
      return;
    }
    if (useMock) {
      setTimeout(() => {
        setConnected((s) => ({ ...s, [provider]: true }));
        toast({ title: `${provider} connected (mock)` });
      }, 600);
      return;
    }

    try {
      const backendBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace(/\/$/, '');
      const fullUrl = url.startsWith('/') ? `${backendBase}${url}` : `${backendBase}/${url}`;

      const features = 'width=600,height=700,menubar=no,toolbar=no,location=no,resizable=yes,scrollbars=yes';
      const w = window.open(fullUrl, `raamp_oauth_${provider}`, features);
      if (!w) {
        toast({ title: 'Popup blocked', description: 'Please allow popups for this site.', variant: 'destructive' });
        return;
      }
      toast({ title: 'OAuth started', description: `Follow the ${provider} flow in the opened tab.` });
      // Listen for popup -> opener postMessage events for faster UX
      const messageHandler = (ev: MessageEvent) => {
        try {
          const data = ev.data || {};
          if (data.provider === provider && data.success) {
            try { w.close(); } catch {}
            window.removeEventListener('message', messageHandler);
            // refresh connections and notify
            fetchConnections();
            toast({ title: `${provider} connected` });
            // also set local state optimistically
            setConnected((s) => ({ ...s, [provider]: true }));
            if (onSuccess) {
              try { onSuccess(); } catch (e) { /* ignore */ }
            }
          }
        } catch (e) {
          // ignore
        }
      };
      window.addEventListener('message', messageHandler);
      const start = Date.now();
      const poll = setInterval(async () => {
        try {
          let ok = false;
          if (provider === 'facebook') {
            const r: any = await apiClient.get('/profile/connections/facebook');
            ok = !!r?.connected;
          } else if (provider === 'instagram') {
            const r: any = await apiClient.get('/profile/connections/instagram');
            ok = !!r?.connected;
          } else if (provider === 'google') {
            const r: any = await apiClient.get('/profile/connections/google-business');
            ok = !!r?.connected;
          }
          if (ok) {
            clearInterval(poll);
            try { w.close(); } catch {}
            await fetchConnections();
                toast({ title: `${provider} connected` });
                if (onSuccess) {
                  try { onSuccess(); } catch (e) { /* ignore */ }
                }
          }
        } catch (err) {
          // ignore
        }

        if (Date.now() - start > 60_000) {
          clearInterval(poll);
        }
      }, 2500);
    } catch (err) {
      toast({ title: 'Connection failed', description: String(err), variant: 'destructive' });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-card to-background flex items-center justify-center p-4">
      <div className="w-full max-w-5xl space-y-8">
        <div className="text-center space-y-4">
          <div className="flex justify-center mb-4">
            <img src={raampIcon} alt="RAAMP" className="h-28 w-28" />
          </div>
          <h1 className="text-4xl font-bold">Secure & Seamless Onboarding</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Dive into the future of marketing automation with RAAMP. Secure your account, connect your essential tools, and set up the platform.
          </p>
        </div>

        <Card className="p-8 card-shadow bg-card/80 backdrop-blur-sm border-primary/20">
          <h2 className="text-2xl font-bold mb-6 text-center">Connect Your Ecosystem</h2>
          <p className="text-muted-foreground text-center mb-8">
            Integrate seamlessly with your favorite platforms. Empower your RAAMP experience by connecting your vital business tools and data sources with just a few clicks.
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Google Maps */}
            <div className="p-6 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-all text-center">
              <div className="w-16 h-16 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Map className="w-8 h-8 text-primary" />
              </div>
              <h3 className="font-bold mb-2">Google Maps</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Enable local business presence and geo-targeted campaigns
              </p>
              <Button
                variant="hero"
                className="w-full"
                onClick={() => openAuthWindowAndPoll('/profile/onboarding/google-maps/connect', 'google')}
              >
                {connected.google ? 'Connected' : 'Connect'}
              </Button>
            </div>

            {/* Facebook */}
            <div className="p-6 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-all text-center">
              <div className="w-16 h-16 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Facebook className="w-8 h-8 text-primary" />
              </div>
              <h3 className="font-bold mb-2">Facebook</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Sync your Facebook Ads and unlock powerful audience insights
              </p>
              <Button
                variant="hero"
                className="w-full"
                onClick={() => openAuthWindowAndPoll('/profile/onboarding/facebook/auth', 'facebook')}
              >
                {connected.facebook ? 'Connected' : 'Connect'}
              </Button>
            </div>

            {/* Instagram */}
            <div className="p-6 bg-muted/50 rounded-lg border border-primary/10 hover:border-primary/30 transition-all text-center">
              <div className="w-16 h-16 rounded-lg bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Instagram className="w-8 h-8 text-primary" />
              </div>
              <h3 className="font-bold mb-2">Instagram</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create and manage Instagram campaigns with AI-powered content
              </p>
              <Button
                variant="hero"
                className="w-full"
                disabled={connected.instagram}
                onClick={async () => {
                  if (!connected.facebook && !useMock) {
                    toast({ title: 'Facebook required', description: 'Connect Facebook first to link Instagram.', variant: 'destructive' });
                    return;
                  }

                  if (useMock) {
                    setTimeout(() => {
                      setConnected((s) => ({ ...s, instagram: true }));
                      toast({ title: 'instagram connected (mock)' });
                    }, 600);
                    return;
                  }

                  // Pre-checks: fetch pages and ensure at least one page has a linked Instagram
                  try {
                    const resp: any = await apiClient.get('/profile/onboarding/instagram/pages');
                    const pages = resp?.pages || [];
                    if (!Array.isArray(pages) || pages.length === 0) {
                      toast({
                        title: 'No Facebook Pages found',
                        description: 'We could not find any Facebook Pages on your account. Create or add a Page, then try again.',
                        variant: 'destructive',
                      });
                      return;
                    }

                    const pagesWithIG = pages.filter((p: any) => p.has_instagram);

                    // If any linked IG account is not Business/Creator, prompt to convert.
                    // We still allow the user to proceed to the page picker; the backend
                    // will enforce actual linkage and account type.
                    const nonProfessional = pagesWithIG.find((p: any) => {
                      const acct = p.instagram;
                      const type = acct?.account_type || acct?.accountType || '';
                      if (!type) return false;
                      const t = String(type).toLowerCase();
                      return !(t.includes('business') || t.includes('creator'));
                    });
                    if (nonProfessional) {
                      const convert = window.confirm('Your Instagram must be Business or Creator to continue. Convert now?');
                      if (!convert) return;
                      window.open('https://help.instagram.com/1533933820244654', '_blank');
                    }

                    // Always show the pages modal so user can pick which Page to link.
                    // The backend will validate whether the selected page actually has
                    // an Instagram Business/Creator account linked and return clear errors.
                    setPagesList(pages);
                    setPagesModalOpen(true);
                  } catch (err: any) {
                    console.error('Pages pre-check failed', err);
                    toast({ title: 'Unable to check pages', description: 'Please ensure Facebook is connected and try again.', variant: 'destructive' });
                  }
                }}
              >
                {connected.instagram ? 'Connected' : 'Connect'}
              </Button>
            </div>
          </div>

          <div className="mt-8 flex justify-center">
            <Link to="/profile/business-setup">
              <Button
                variant="hero"
                size="lg"
                disabled={!connected.facebook || !connected.instagram || !connected.google}
                title={
                  !connected.facebook || !connected.instagram || !connected.google
                    ? 'Connect Google Maps, Facebook and Instagram to continue'
                    : 'Continue to Business Setup'
                }
              >
                Continue to Business Setup
              </Button>
            </Link>
          </div>
        </Card>

        <MapsConnectModal
          isOpen={mapsModalOpen}
          onClose={() => setMapsModalOpen(false)}
          onConnected={(payload) => {
            setConnected((s) => ({ ...s, google: true }));
            toast({ title: 'Google Maps connected' });
            fetchConnections();
          }}
        />

        {/* Help modal when no Instagram-linked Pages are found */}
        {linkHelpOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-card p-6 rounded-lg w-full max-w-lg">
              <h3 className="text-lg font-bold mb-2">Link a Facebook Page to Instagram</h3>
              <p className="text-sm text-muted-foreground mb-4">
                We couldn&apos;t find any Facebook Pages that are currently linked to an Instagram Business or Creator account.
                To continue, link one of your Pages to Instagram in Meta, then return here and retry the connection.
              </p>
              {pagesList && pagesList.length > 0 && (
                <div className="mb-4 space-y-2 max-h-40 overflow-auto">
                  {pagesList.map((p: any) => (
                    <div key={p.id} className="flex items-center justify-between p-2 bg-muted/40 rounded">
                      <div>
                        <div className="font-semibold text-sm">{p.name}</div>
                        <div className="text-xs text-muted-foreground">Page ID: {p.id}</div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          // Open the Page in a new tab so the user can manage Instagram linking.
                          window.open(`https://www.facebook.com/${p.id}`, '_blank');
                        }}
                      >
                        Open Page
                      </Button>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex justify-between gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    window.open('https://help.instagram.com/1533933820244654', '_blank');
                  }}
                >
                  Open Meta Help
                </Button>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    onClick={() => setLinkHelpOpen(false)}
                  >
                    Close
                  </Button>
                  <Button
                    onClick={() => {
                      setLinkHelpOpen(false);
                      // Re-run connection checks so user can continue after linking.
                      fetchConnections();
                    }}
                  >
                    I&apos;ve linked my account
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pages modal - simple themed modal to choose a Facebook page to link Instagram */}
        {pagesModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-card p-6 rounded-lg w-full max-w-lg">
              <h3 className="text-lg font-bold mb-4">Select a Facebook Page</h3>
              <div className="space-y-3 max-h-64 overflow-auto">
                {pagesList.map((p: any) => {
                  const linkPage = async (pageId: string) => {
                    try {
                      await apiClient.get(`/profile/onboarding/instagram/accounts?page_id=${pageId}`);
                      setPagesModalOpen(false);
                      setConnected((s) => ({ ...s, instagram: true }));
                      toast({ title: 'Instagram account connected successfully' });
                      // refresh connections
                      fetchConnections();
                    } catch (err: any) {
                      console.error('Link IG error', err);
                      // If backend indicates missing permissions, show clear message
                      const isMissing = err && (err.error === 'missing_permissions' || Array.isArray(err.missing) || (err?.detail && err.detail?.missing));
                      if (isMissing) {
                        toast({ 
                          title: 'Missing Instagram Permissions', 
                          description: 'Please ensure Instagram Business account permissions are enabled in your Facebook Business settings, then reconnect Facebook.', 
                          variant: 'destructive' 
                        });
                        return;
                      }
                      // If no IG linked
                      if (err && err.status === 404) {
                        toast({ title: 'No Instagram linked to this Page.', variant: 'destructive' });
                        return;
                      }
                      toast({ title: 'Link failed', description: err.message || String(err), variant: 'destructive' });
                    }
                  };

                  return (
                    <div key={p.id} className="flex items-center justify-between p-3 bg-muted/50 rounded">
                      <div>
                        <div className="font-semibold">{p.name}</div>
                        <div className="text-sm text-muted-foreground">{p.id}</div>
                      </div>
                      <div>
                        <Button size="sm" onClick={() => linkPage(p.id)}>
                          Link
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex justify-end">
                <Button variant="ghost" onClick={() => setPagesModalOpen(false)}>Cancel</Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Onboarding;
