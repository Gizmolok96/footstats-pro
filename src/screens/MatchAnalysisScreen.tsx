import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRoute, useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { Colors } from '../constants/colors';
import { apiFetch } from '../lib/api';
import { saveToHistory } from './HistoryScreen';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withDelay,
} from 'react-native-reanimated';

// Types
interface TeamStat {
  goals_for: number;
  goals_against: number;
  result: 'W' | 'D' | 'L';
  is_home: boolean;
  date: string;
  opponent: string;
}

interface TeamFeatures {
  pointsPerGame: number;
  winRate: number;
  avgGoalsFor: number;
  avgGoalsAgainst: number;
  xgForAvg: number;
  avgPossession: number;
  avgShots: number;
  recentPoints: number;
  trend: number;
  totalMatches: number;
  formString: string;
}

interface H2HStats {
  homeWins: number;
  draws: number;
  awayWins: number;
  total: number;
  avgGoals: number;
  matches: {
    homeTeam: { id: number; name: string };
    awayTeam: { id: number; name: string };
    homeResult: number;
    awayResult: number;
    date: string;
  }[];
}

interface BettingTip {
  market: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

interface Analysis {
  homeXg: number;
  awayXg: number;
  homeWinPct: number;
  drawPct: number;
  awayWinPct: number;
  mostLikelyScore: string;
  mostLikelyProb: number;
  over25Pct: number;
  bttsPct: number;
  expectedTotal: number;
  homeFeatures: TeamFeatures;
  awayFeatures: TeamFeatures;
  h2h: H2HStats;
  bettingTips: BettingTip[];
  keyFactors: string[];
  confidenceScore: number;
  leagueContext: { avgGoals: number; homeAdvantage: number; style: string };
}

interface MatchData {
  match: {
    id: number;
    date: string;
    homeTeam: { id: number; name: string };
    awayTeam: { id: number; name: string };
    league: string;
    status: string;
    homeResult: number | null;
    awayResult: number | null;
  };
  analysis: Analysis;
  homeRecentMatches: TeamStat[];
  awayRecentMatches: TeamStat[];
}

// Animated Probability Bar
function AnimatedBar({ pct, color, delay }: { pct: number; color: string; delay: number }) {
  const width = useSharedValue(0);

  useEffect(() => {
    width.value = withDelay(delay, withTiming(pct, { duration: 800 }));
  }, [pct]);

  const animStyle = useAnimatedStyle(() => ({
    width: `${width.value}%`,
  }));

  return (
    <View style={aStyles.barTrack}>
      <Animated.View style={[aStyles.barFill, { backgroundColor: color }, animStyle]} />
    </View>
  );
}

// Section Container
function Section({ title, children, icon }: { title: string; children: React.ReactNode; icon?: string }) {
  return (
    <View style={sStyles.section}>
      <View style={sStyles.sectionHeader}>
        {icon && <Icon name={icon} size={15} color={Colors.accent} />}
        <Text style={sStyles.sectionTitle}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

// Form Badge
function FormBadge({ result }: { result: 'W' | 'D' | 'L' }) {
  const bg = result === 'W' ? Colors.accentDim : result === 'D' ? Colors.amberDim : Colors.redDim;
  const fg = result === 'W' ? Colors.win : result === 'D' ? Colors.draw : Colors.loss;
  return (
    <View style={[fStyles.badge, { backgroundColor: bg }]}>
      <Text style={[fStyles.badgeText, { color: fg }]}>{result}</Text>
    </View>
  );
}

// Team Form Row
function TeamFormRow({ name, stats, isHome }: { name: string; stats: TeamStat[]; isHome: boolean }) {
  const last5 = stats.slice(0, 5);
  return (
    <View style={fStyles.teamFormRow}>
      <View style={[fStyles.teamDot, { backgroundColor: isHome ? Colors.home : Colors.away }]} />
      <Text style={fStyles.teamLabel} numberOfLines={1}>{name}</Text>
      <View style={fStyles.badgeRow}>
        {last5.map((s, i) => (
          <FormBadge key={i} result={s.result} />
        ))}
        {Array.from({ length: Math.max(0, 5 - last5.length) }).map((_, i) => (
          <View key={`empty-${i}`} style={[fStyles.badge, { backgroundColor: Colors.border }]}>
            <Text style={[fStyles.badgeText, { color: Colors.textMuted }]}>-</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

// Stat Compare
function StatCompare({
  label,
  homeVal,
  awayVal,
  format,
}: {
  label: string;
  homeVal: number;
  awayVal: number;
  format: (v: number) => string;
}) {
  const total = homeVal + awayVal;
  const homePct = total > 0 ? (homeVal / total) * 100 : 50;
  const awayPct = 100 - homePct;

  return (
    <View style={statStyles.row}>
      <Text style={statStyles.homeVal}>{format(homeVal)}</Text>
      <View style={statStyles.mid}>
        <Text style={statStyles.label}>{label}</Text>
        <View style={statStyles.barWrap}>
          <View style={[statStyles.barHome, { flex: homePct }]} />
          <View style={[statStyles.barAway, { flex: awayPct }]} />
        </View>
      </View>
      <Text style={statStyles.awayVal}>{format(awayVal)}</Text>
    </View>
  );
}

export default function MatchAnalysisScreen() {
  const route = useRoute();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { id } = route.params as { id: string };
  const [activeTab, setActiveTab] = useState<'analysis' | 'form' | 'h2h'>('analysis');

  const { data, isLoading, isError, refetch } = useQuery<MatchData>({
    queryKey: ['/api/match', id, 'analyze'],
    queryFn: async () => {
      const res = await apiFetch(`/api/match/${id}/analyze`);
      if (!res.ok) throw new Error('Analysis failed');
      return res.json();
    },
    staleTime: 10 * 60 * 1000,
  });

  useEffect(() => {
    if (data) {
      const m = data.match;
      const a = data.analysis;
      saveToHistory({
        matchId: m.id,
        homeTeam: m.homeTeam?.name || 'Home',
        awayTeam: m.awayTeam?.name || 'Away',
        league: typeof m.league === 'string' ? m.league : 'Unknown',
        date: m.date,
        analyzedAt: new Date().toISOString(),
        homeWinPct: a.homeWinPct,
        drawPct: a.drawPct,
        awayWinPct: a.awayWinPct,
        mostLikelyScore: a.mostLikelyScore,
        over25Pct: a.over25Pct,
        bttsPct: a.bttsPct,
        homeResult: m.homeResult,
        awayResult: m.awayResult,
        status: String(m.status),
      });
    }
  }, [data]);

  const renderHeader = () => {
    const match = data?.match;
    const analysis = data?.analysis;
    const homeName = match?.homeTeam?.name || 'Home';
    const awayName = match?.awayTeam?.name || 'Away';
    const hasScore = match?.homeResult !== null && match?.awayResult !== null;

    return (
      <View style={styles.matchHeader}>
        <View style={styles.leaguePill}>
          <Icon name="football" size={11} color={Colors.accent} />
          <Text style={styles.leaguePillText} numberOfLines={1}>
            {typeof match?.league === 'string' ? match.league : 'Football'}
          </Text>
        </View>

        <View style={styles.teamsSection}>
          <View style={styles.teamColumn}>
            <View style={[styles.teamAvatar, { backgroundColor: Colors.blueDim }]}>
              <Text style={styles.teamAvatarText}>{homeName.slice(0, 2).toUpperCase()}</Text>
            </View>
            <Text style={styles.teamNameBig} numberOfLines={2}>{homeName}</Text>
          </View>

          <View style={styles.scoreMid}>
            {hasScore ? (
              <Text style={styles.finalScore}>
                {match?.homeResult} - {match?.awayResult}
              </Text>
            ) : (
              <Text style={styles.vsText}>VS</Text>
            )}
            {analysis && (
              <View style={styles.confidencePill}>
                <Text style={styles.confidenceText}>{analysis.confidenceScore}% confidence</Text>
              </View>
            )}
          </View>

          <View style={[styles.teamColumn, styles.teamColumnRight]}>
            <View style={[styles.teamAvatar, { backgroundColor: '#3B1F5F' }]}>
              <Text style={styles.teamAvatarText}>{awayName.slice(0, 2).toUpperCase()}</Text>
            </View>
            <Text style={[styles.teamNameBig, { textAlign: 'right' }]} numberOfLines={2}>
              {awayName}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  const renderTabs = () => (
    <View style={styles.tabBar}>
      {(['analysis', 'form', 'h2h'] as const).map((t) => (
        <Pressable
          key={t}
          onPress={() => setActiveTab(t)}
          style={[styles.tab, activeTab === t && styles.tabActive]}>
          <Text style={[styles.tabText, activeTab === t && styles.tabTextActive]}>
            {t === 'analysis' ? 'Analysis' : t === 'form' ? 'Team Form' : 'H2H'}
          </Text>
        </Pressable>
      ))}
    </View>
  );

  const renderAnalysis = (analysis: Analysis, homeTeam: string, awayTeam: string) => (
    <View style={styles.tabContent}>
      <Section title="Win Probability" icon="pie-chart-outline">
        <View style={styles.probContainer}>
          <View style={styles.probRow}>
            <Text style={styles.probLabel}>{homeTeam}</Text>
            <Text style={[styles.probPct, { color: Colors.home }]}>{analysis.homeWinPct.toFixed(0)}%</Text>
          </View>
          <AnimatedBar pct={analysis.homeWinPct} color={Colors.home} delay={0} />

          <View style={[styles.probRow, { marginTop: 10 }]}>
            <Text style={styles.probLabel}>Draw</Text>
            <Text style={[styles.probPct, { color: Colors.amber }]}>{analysis.drawPct.toFixed(0)}%</Text>
          </View>
          <AnimatedBar pct={analysis.drawPct} color={Colors.amber} delay={100} />

          <View style={[styles.probRow, { marginTop: 10 }]}>
            <Text style={styles.probLabel}>{awayTeam}</Text>
            <Text style={[styles.probPct, { color: Colors.away }]}>{analysis.awayWinPct.toFixed(0)}%</Text>
          </View>
          <AnimatedBar pct={analysis.awayWinPct} color={Colors.away} delay={200} />
        </View>
      </Section>

      <Section title="Score Prediction" icon="football-outline">
        <View style={styles.marketGrid}>
          <View style={styles.marketCardBig}>
            <Text style={styles.marketLabel}>Most Likely Score</Text>
            <Text style={styles.marketScoreValue}>{analysis.mostLikelyScore}</Text>
            <Text style={styles.marketSub}>{analysis.mostLikelyProb.toFixed(0)}% probability</Text>
          </View>
          <View style={styles.marketCard}>
            <Text style={styles.marketLabel}>Expected Total</Text>
            <Text style={styles.marketValue}>{analysis.expectedTotal}</Text>
            <Text style={styles.marketSub}>goals</Text>
          </View>
          <View style={styles.marketCard}>
            <Text style={styles.marketLabel}>Over 2.5</Text>
            <Text style={[styles.marketValue, { color: analysis.over25Pct > 55 ? Colors.accent : Colors.textSecondary }]}>
              {analysis.over25Pct.toFixed(0)}%
            </Text>
          </View>
          <View style={styles.marketCard}>
            <Text style={styles.marketLabel}>BTTS</Text>
            <Text style={[styles.marketValue, { color: analysis.bttsPct > 55 ? Colors.accent : Colors.textSecondary }]}>
              {analysis.bttsPct.toFixed(0)}%
            </Text>
          </View>
          <View style={styles.marketCard}>
            <Text style={styles.marketLabel}>Home xG</Text>
            <Text style={[styles.marketValue, { color: Colors.home }]}>{analysis.homeXg}</Text>
          </View>
          <View style={styles.marketCard}>
            <Text style={styles.marketLabel}>Away xG</Text>
            <Text style={[styles.marketValue, { color: Colors.away }]}>{analysis.awayXg}</Text>
          </View>
        </View>
      </Section>

      <Section title="Team Stats" icon="bar-chart-outline">
        <View style={styles.statsHeader}>
          <Text style={[styles.statsTeamLabel, { color: Colors.home }]} numberOfLines={1}>{homeTeam}</Text>
          <View style={{ flex: 1 }} />
          <Text style={[styles.statsTeamLabel, { color: Colors.away, textAlign: 'right' }]} numberOfLines={1}>{awayTeam}</Text>
        </View>
        <StatCompare label="Goals/Game" homeVal={analysis.homeFeatures.avgGoalsFor} awayVal={analysis.awayFeatures.avgGoalsFor} format={(v) => v.toFixed(1)} />
        <StatCompare label="xG/Game" homeVal={analysis.homeFeatures.xgForAvg} awayVal={analysis.awayFeatures.xgForAvg} format={(v) => v.toFixed(2)} />
        <StatCompare label="Possession" homeVal={analysis.homeFeatures.avgPossession} awayVal={analysis.awayFeatures.avgPossession} format={(v) => `${v.toFixed(0)}%`} />
        <StatCompare label="Shots/Game" homeVal={analysis.homeFeatures.avgShots} awayVal={analysis.awayFeatures.avgShots} format={(v) => v.toFixed(1)} />
        <StatCompare label="PPG" homeVal={analysis.homeFeatures.pointsPerGame} awayVal={analysis.awayFeatures.pointsPerGame} format={(v) => v.toFixed(2)} />
      </Section>

      {analysis.bettingTips.length > 0 && (
        <Section title="Betting Tips" icon="bulb-outline">
          {analysis.bettingTips.map((tip, i) => (
            <View key={i} style={styles.tipCard}>
              <View
                style={[
                  styles.tipConfBadge,
                  {
                    backgroundColor:
                      tip.confidence === 'high' ? Colors.accentDim
                      : tip.confidence === 'medium' ? Colors.amberDim
                      : Colors.redDim,
                  },
                ]}>
                <Text
                  style={[
                    styles.tipConfText,
                    {
                      color:
                        tip.confidence === 'high' ? Colors.accent
                        : tip.confidence === 'medium' ? Colors.amber
                        : Colors.red,
                    },
                  ]}>
                  {tip.confidence.toUpperCase()}
                </Text>
              </View>
              <View style={styles.tipBody}>
                <Text style={styles.tipMarket}>{tip.market}</Text>
                <Text style={styles.tipReason}>{tip.reason}</Text>
              </View>
            </View>
          ))}
          <View style={styles.disclaimer}>
            <Icon name="alert-circle-outline" size={12} color={Colors.textMuted} />
            <Text style={styles.disclaimerText}>For informational purposes only. Gamble responsibly.</Text>
          </View>
        </Section>
      )}

      <Section title="Key Factors" icon="key-outline">
        {analysis.keyFactors.map((f, i) => (
          <View key={i} style={styles.factorRow}>
            <View style={styles.factorDot} />
            <Text style={styles.factorText}>{f}</Text>
          </View>
        ))}
        <View style={styles.leagueCtxRow}>
          <Icon name="information-circle-outline" size={12} color={Colors.textMuted} />
          <Text style={styles.leagueCtxText}>
            League avg: {analysis.leagueContext.avgGoals} goals/game · {analysis.leagueContext.style} style
          </Text>
        </View>
      </Section>
    </View>
  );

  const renderForm = (homeMatches: TeamStat[], awayMatches: TeamStat[], homeTeam: string, awayTeam: string) => (
    <View style={styles.tabContent}>
      <Section title="Last 5 Matches" icon="time-outline">
        <TeamFormRow name={homeTeam} stats={homeMatches} isHome />
        <View style={{ height: 8 }} />
        <TeamFormRow name={awayTeam} stats={awayMatches} isHome={false} />
      </Section>

      <Section title={`${homeTeam} Recent`} icon="home-outline">
        {homeMatches.slice(0, 5).map((m, i) => (
          <View key={i} style={styles.recentRow}>
            <FormBadge result={m.result} />
            <View style={styles.recentInfo}>
              <Text style={styles.recentOpponent} numberOfLines={1}>
                {m.is_home ? 'vs' : '@'} {m.opponent}
              </Text>
              <Text style={styles.recentDate}>
                {m.date ? new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
              </Text>
            </View>
            <Text style={styles.recentScore}>{m.goals_for} - {m.goals_against}</Text>
          </View>
        ))}
        {homeMatches.length === 0 && <Text style={styles.noDataText}>No recent data available</Text>}
      </Section>

      <Section title={`${awayTeam} Recent`} icon="airplane-outline">
        {awayMatches.slice(0, 5).map((m, i) => (
          <View key={i} style={styles.recentRow}>
            <FormBadge result={m.result} />
            <View style={styles.recentInfo}>
              <Text style={styles.recentOpponent} numberOfLines={1}>
                {m.is_home ? 'vs' : '@'} {m.opponent}
              </Text>
              <Text style={styles.recentDate}>
                {m.date ? new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
              </Text>
            </View>
            <Text style={styles.recentScore}>{m.goals_for} - {m.goals_against}</Text>
          </View>
        ))}
        {awayMatches.length === 0 && <Text style={styles.noDataText}>No recent data available</Text>}
      </Section>
    </View>
  );

  const renderH2H = (analysis: Analysis, homeTeam: string, awayTeam: string) => {
    const h2h = analysis.h2h;
    return (
      <View style={styles.tabContent}>
        <Section title="Head to Head Summary" icon="swap-horizontal-outline">
          {h2h.total === 0 ? (
            <Text style={styles.noDataText}>No recent H2H matches found</Text>
          ) : (
            <>
              <View style={styles.h2hSummaryRow}>
                <View style={styles.h2hItem}>
                  <Text style={[styles.h2hCount, { color: Colors.home }]}>{h2h.homeWins}</Text>
                  <Text style={styles.h2hLabel}>{homeTeam}</Text>
                </View>
                <View style={styles.h2hItem}>
                  <Text style={[styles.h2hCount, { color: Colors.amber }]}>{h2h.draws}</Text>
                  <Text style={styles.h2hLabel}>Draws</Text>
                </View>
                <View style={styles.h2hItem}>
                  <Text style={[styles.h2hCount, { color: Colors.away }]}>{h2h.awayWins}</Text>
                  <Text style={styles.h2hLabel}>{awayTeam}</Text>
                </View>
              </View>
              <View style={styles.h2hBar}>
                <View style={[styles.h2hBarHome, { flex: h2h.homeWins + 0.01 }]} />
                <View style={[styles.h2hBarDraw, { flex: h2h.draws + 0.01 }]} />
                <View style={[styles.h2hBarAway, { flex: h2h.awayWins + 0.01 }]} />
              </View>
              <View style={styles.h2hAvgRow}>
                <Icon name="football-outline" size={13} color={Colors.textMuted} />
                <Text style={styles.h2hAvgText}>
                  Average {h2h.avgGoals.toFixed(1)} goals per match over {h2h.total} meetings
                </Text>
              </View>
            </>
          )}
        </Section>

        {h2h.matches?.length > 0 && (
          <Section title="Recent Meetings" icon="list-outline">
            {h2h.matches.map((m, i) => (
              <View key={i} style={styles.h2hMatch}>
                <Text style={styles.h2hMatchDate}>
                  {m.date ? new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}
                </Text>
                <View style={styles.h2hMatchTeams}>
                  <Text style={styles.h2hMatchTeam} numberOfLines={1}>{m.homeTeam?.name}</Text>
                  <Text style={styles.h2hMatchScore}>{m.homeResult} - {m.awayResult}</Text>
                  <Text style={[styles.h2hMatchTeam, { textAlign: 'right' }]} numberOfLines={1}>{m.awayTeam?.name}</Text>
                </View>
              </View>
            ))}
          </Section>
        )}
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.navBar}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Icon name="arrow-back" size={22} color={Colors.text} />
        </Pressable>
        <Text style={styles.navTitle}>Match Analysis</Text>
        <View style={{ width: 40 }} />
      </View>

      {isLoading ? (
        <View style={styles.loadingState}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingTitle}>Analyzing match...</Text>
          <Text style={styles.loadingSubtitle}>Fetching team stats, running Poisson model</Text>
        </View>
      ) : isError ? (
        <View style={styles.errorState}>
          <Icon name="cloud-offline-outline" size={52} color={Colors.textMuted} />
          <Text style={styles.errorTitle}>Analysis failed</Text>
          <Text style={styles.errorSubtitle}>Check your connection and try again</Text>
          <Pressable style={styles.retryBtn} onPress={() => refetch()}>
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      ) : data ? (
        <>
          {renderHeader()}
          {renderTabs()}
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: insets.bottom + 20 }}>
            {activeTab === 'analysis' && renderAnalysis(data.analysis, data.match.homeTeam?.name || 'Home', data.match.awayTeam?.name || 'Away')}
            {activeTab === 'form' && renderForm(data.homeRecentMatches, data.awayRecentMatches, data.match.homeTeam?.name || 'Home', data.match.awayTeam?.name || 'Away')}
            {activeTab === 'h2h' && renderH2H(data.analysis, data.match.homeTeam?.name || 'Home', data.match.awayTeam?.name || 'Away')}
          </ScrollView>
        </>
      ) : null}
    </View>
  );
}

const aStyles = StyleSheet.create({
  barTrack: { height: 8, backgroundColor: Colors.border, borderRadius: 4, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 4 },
});

const sStyles = StyleSheet.create({
  section: { marginHorizontal: 12, marginBottom: 16, backgroundColor: Colors.bgCard, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: Colors.border },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 14 },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: Colors.text },
});

const fStyles = StyleSheet.create({
  badge: { width: 26, height: 26, borderRadius: 6, alignItems: 'center', justifyContent: 'center' },
  badgeText: { fontSize: 12, fontWeight: '700' },
  teamFormRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  teamDot: { width: 8, height: 8, borderRadius: 4 },
  teamLabel: { fontSize: 13, fontWeight: '500', color: Colors.text, flex: 1 },
  badgeRow: { flexDirection: 'row', gap: 4 },
});

const statStyles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 10, gap: 8 },
  homeVal: { fontSize: 13, fontWeight: '600', color: Colors.home, width: 48, textAlign: 'left' },
  awayVal: { fontSize: 13, fontWeight: '600', color: Colors.away, width: 48, textAlign: 'right' },
  mid: { flex: 1, gap: 4 },
  label: { fontSize: 11, color: Colors.textMuted, textAlign: 'center' },
  barWrap: { height: 5, borderRadius: 3, flexDirection: 'row', overflow: 'hidden', gap: 1 },
  barHome: { backgroundColor: Colors.home, borderRadius: 3 },
  barAway: { backgroundColor: Colors.away, borderRadius: 3 },
});

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  navBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 12, paddingVertical: 10 },
  backBtn: { width: 40, height: 40, borderRadius: 12, backgroundColor: Colors.bgCard, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: Colors.border },
  navTitle: { fontSize: 16, fontWeight: '600', color: Colors.text },
  matchHeader: { paddingHorizontal: 12, paddingBottom: 16 },
  leaguePill: { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'center', backgroundColor: Colors.accentDim, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20, marginBottom: 16 },
  leaguePillText: { fontSize: 11, fontWeight: '500', color: Colors.accent, maxWidth: 220 },
  teamsSection: { flexDirection: 'row', alignItems: 'center' },
  teamColumn: { flex: 1, alignItems: 'flex-start', gap: 8 },
  teamColumnRight: { alignItems: 'flex-end' },
  teamAvatar: { width: 52, height: 52, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  teamAvatarText: { fontSize: 16, fontWeight: '700', color: Colors.text },
  teamNameBig: { fontSize: 15, fontWeight: '700', color: Colors.text, maxWidth: 110 },
  scoreMid: { alignItems: 'center', gap: 6, paddingHorizontal: 8 },
  finalScore: { fontSize: 28, fontWeight: '700', color: Colors.text },
  vsText: { fontSize: 20, fontWeight: '700', color: Colors.textMuted },
  confidencePill: { backgroundColor: Colors.accentDim, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  confidenceText: { fontSize: 10, fontWeight: '500', color: Colors.accent },
  tabBar: { flexDirection: 'row', marginHorizontal: 12, marginBottom: 10, backgroundColor: Colors.bgCard, borderRadius: 12, padding: 4, gap: 2 },
  tab: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 10 },
  tabActive: { backgroundColor: Colors.bgSecondary },
  tabText: { fontSize: 13, fontWeight: '500', color: Colors.textMuted },
  tabTextActive: { color: Colors.text, fontWeight: '600' },
  tabContent: { paddingTop: 4 },
  probContainer: { gap: 0 },
  probRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  probLabel: { fontSize: 13, fontWeight: '500', color: Colors.text, flex: 1 },
  probPct: { fontSize: 16, fontWeight: '700', marginLeft: 8 },
  marketGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  marketCardBig: { width: '100%', backgroundColor: Colors.bgCardDark, borderRadius: 10, padding: 14, borderWidth: 1, borderColor: Colors.border, alignItems: 'center' },
  marketCard: { flex: 1, minWidth: '46%', backgroundColor: Colors.bgCardDark, borderRadius: 10, padding: 12, borderWidth: 1, borderColor: Colors.border, alignItems: 'center' },
  marketLabel: { fontSize: 11, color: Colors.textMuted, marginBottom: 4 },
  marketScoreValue: { fontSize: 32, fontWeight: '700', color: Colors.text },
  marketValue: { fontSize: 22, fontWeight: '700', color: Colors.text },
  marketSub: { fontSize: 11, color: Colors.textMuted, marginTop: 2 },
  statsHeader: { flexDirection: 'row', marginBottom: 12 },
  statsTeamLabel: { fontSize: 12, fontWeight: '600', flex: 1 },
  tipCard: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, marginBottom: 10, backgroundColor: Colors.bgCardDark, borderRadius: 10, padding: 12, borderWidth: 1, borderColor: Colors.border },
  tipConfBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  tipConfText: { fontSize: 10, fontWeight: '700' },
  tipBody: { flex: 1, gap: 2 },
  tipMarket: { fontSize: 13, fontWeight: '600', color: Colors.text },
  tipReason: { fontSize: 12, color: Colors.textMuted },
  disclaimer: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 4, paddingTop: 10, borderTopWidth: 1, borderTopColor: Colors.border },
  disclaimerText: { fontSize: 11, color: Colors.textMuted, flex: 1 },
  factorRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  factorDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.accent },
  factorText: { fontSize: 13, color: Colors.textSecondary, flex: 1 },
  leagueCtxRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 8, paddingTop: 10, borderTopWidth: 1, borderTopColor: Colors.border },
  leagueCtxText: { fontSize: 11, color: Colors.textMuted, flex: 1 },
  recentRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  recentInfo: { flex: 1 },
  recentOpponent: { fontSize: 13, fontWeight: '500', color: Colors.text },
  recentDate: { fontSize: 11, color: Colors.textMuted },
  recentScore: { fontSize: 14, fontWeight: '600', color: Colors.text, minWidth: 40, textAlign: 'right' },
  noDataText: { fontSize: 13, color: Colors.textMuted, textAlign: 'center', paddingVertical: 8 },
  h2hSummaryRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  h2hItem: { alignItems: 'center', gap: 4 },
  h2hCount: { fontSize: 28, fontWeight: '700' },
  h2hLabel: { fontSize: 12, color: Colors.textMuted },
  h2hBar: { height: 6, borderRadius: 3, flexDirection: 'row', overflow: 'hidden', gap: 1, marginBottom: 10 },
  h2hBarHome: { backgroundColor: Colors.home, borderRadius: 3 },
  h2hBarDraw: { backgroundColor: Colors.amber, borderRadius: 3 },
  h2hBarAway: { backgroundColor: Colors.away, borderRadius: 3 },
  h2hAvgRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  h2hAvgText: { fontSize: 12, color: Colors.textMuted, flex: 1 },
  h2hMatch: { marginBottom: 10, paddingBottom: 10, borderBottomWidth: 1, borderBottomColor: Colors.border },
  h2hMatchDate: { fontSize: 11, color: Colors.textMuted, marginBottom: 4 },
  h2hMatchTeams: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  h2hMatchTeam: { fontSize: 13, fontWeight: '500', color: Colors.text, flex: 1 },
  h2hMatchScore: { fontSize: 16, fontWeight: '700', color: Colors.text, minWidth: 48, textAlign: 'center' },
  loadingState: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingTitle: { fontSize: 16, fontWeight: '600', color: Colors.text },
  loadingSubtitle: { fontSize: 13, color: Colors.textMuted },
  errorState: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  errorTitle: { fontSize: 16, fontWeight: '600', color: Colors.text },
  errorSubtitle: { fontSize: 13, color: Colors.textMuted },
  retryBtn: { backgroundColor: Colors.accent, paddingHorizontal: 24, paddingVertical: 10, borderRadius: 10, marginTop: 8 },
  retryText: { fontSize: 14, fontWeight: '600', color: '#fff' },
});
