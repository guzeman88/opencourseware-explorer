"use client";

import { useRef, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { SkipForward, Gauge, Clock, Info } from "lucide-react";
import { cn } from "@/lib/utils";

const ReactPlayer = dynamic(() => import("react-player/youtube"), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-black flex items-center justify-center rounded-lg">
      <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  ),
});

const VIDEO_ID = "YiqIkSHSmyc";
const VIDEO_URL = `https://www.youtube.com/watch?v=${VIDEO_ID}`;
const POSTER = `https://img.youtube.com/vi/${VIDEO_ID}/maxresdefault.jpg`;
const VIDEO_DURATION = 3134; // seconds (~52m 14s)

// Generated with: ffmpeg -i audio.wav -af "silencedetect=n=-40dB:d=0.8" -f null -
// Source: 18.065 Lecture 1 — The Column Space of A Contains All Vectors Ax (YiqIkSHSmyc)
const SILENCE: [number, number][] = [
  [0, 1.583764],
  [20.805374, 23.55619],
  [24.348413, 25.1961],
  [30.027234, 30.831995],
  [44.403605, 46.072789],
  [68.850454, 69.651247],
  [76.183016, 77.039002],
  [96.626961, 97.839093],
  [106.511361, 107.871474],
  [131.357347, 132.422993],
  [136.27254, 137.140295],
  [138.932063, 140.103061],
  [150.98907, 152.036735],
  [160.561315, 161.593673],
  [199.15322, 199.971043],
  [207.736848, 208.704807],
  [219.831905, 221.214422],
  [225.253991, 226.224853],
  [232.719909, 233.696032],
  [244.868254, 245.954308],
  [250.199365, 251.087506],
  [260.566893, 262.769592],
  [284.35585, 285.226372],
  [286.09093, 287.012154],
  [289.676871, 290.494739],
  [299.661814, 302.512086],
  [315.042676, 317.32068],
  [323.01966, 324.457098],
  [344.482562, 345.64644],
  [352.18059, 354.261973],
  [355.471179, 356.650816],
  [359.26415, 360.159955],
  [369.727732, 371.065646],
  [375.089637, 376.790816],
  [377.77102, 379.705986],
  [382.998322, 384.508345],
  [386.926508, 387.74068],
  [389.433764, 390.753923],
  [394.713197, 395.966485],
  [399.908413, 400.910023],
  [401.616054, 402.810045],
  [417.860658, 419.231361],
  [426.180431, 427.024036],
  [427.047959, 428.137347],
  [436.485918, 437.307846],
  [447.502449, 448.846395],
  [462.81737, 464.533107],
  [465.704966, 466.706531],
  [474.015397, 475.04873],
  [476.643741, 477.663107],
  [479.207438, 480.034422],
  [493.859728, 494.803243],
  [498.636803, 500.339274],
  [511.024626, 512.159955],
  [519.405238, 520.442925],
  [536.172063, 537.32263],
  [548.574762, 549.81551],
  [568.3461, 569.395692],
  [572.994558, 574.202857],
  [575.804966, 576.688798],
  [579.679252, 581.30288],
  [582.830272, 584.381156],
  [603.123356, 604.039297],
  [620.567982, 621.945918],
  [627.531519, 628.452698],
  [637.036009, 638.241927],
  [645.916961, 646.885465],
  [650.241542, 651.150204],
  [653.501995, 654.670204],
  [661.987959, 663.661111],
  [682.598685, 683.620181],
  [700.329297, 701.48483],
  [702.802426, 703.671497],
  [726.050952, 727.083084],
  [729.30966, 730.478345],
  [731.903719, 733.172109],
  [736.42644, 738.457347],
  [738.698163, 739.755896],
  [745.032109, 745.950794],
  [747.117778, 748.011814],
  [758.4339, 760.827234],
  [763.54458, 766.097075],
  [775.68483, 777.273197],
  [779.511179, 780.518299],
  [781.083991, 783.609796],
  [790.401905, 791.365374],
  [814.970045, 815.922925],
  [820.217596, 821.283787],
  [821.601837, 823.059025],
  [834.84898, 835.666599],
  [840.093039, 840.989819],
  [848.178163, 848.987052],
  [863.928481, 865.799025],
  [867.377596, 868.313175],
  [883.125533, 885.728639],
  [887.866259, 888.832381],
  [890.736009, 891.746644],
  [895.922562, 898.8922],
  [907.487347, 908.404898],
  [910.12161, 910.923356],
  [913.681995, 914.999206],
  [915.431701, 917.038753],
  [918.25678, 919.767052],
  [921.742585, 923.690181],
  [932.856417, 934.421111],
  [947.268685, 948.283016],
  [950.154762, 951.03415],
  [953.027483, 954.289501],
  [958.429252, 959.272857],
  [960.137415, 961.052313],
  [971.97898, 973.181497],
  [983.54966, 984.751927],
  [985.235828, 986.243152],
  [987.719229, 988.833243],
  [989.583356, 991.072698],
  [995.517438, 996.680703],
  [1001.850159, 1004.007959],
  [1017.323333, 1018.534603],
  [1019.901066, 1021.663923],
  [1028.776485, 1030.735057],
  [1036.343333, 1037.471814],
  [1044.146576, 1046.158413],
  [1046.588095, 1048.027732],
  [1048.639615, 1049.739819],
  [1051.536621, 1052.532041],
  [1053.957891, 1054.831202],
  [1056.243039, 1057.282268],
  [1063.710091, 1064.661315],
  [1069.639683, 1070.496463],
  [1072.768571, 1074.019229],
  [1081.657914, 1082.741406],
  [1086.415193, 1087.522018],
  [1089.113492, 1090.105601],
  [1091.061088, 1093.334286],
  [1095.583129, 1096.911406],
  [1112.221429, 1113.093583],
  [1118.825306, 1121.173923],
  [1125.95483, 1128.614853],
  [1133.500363, 1135.845374],
  [1138.119955, 1139.139615],
  [1141.600839, 1142.974535],
  [1143.898458, 1144.790227],
  [1148.34576, 1149.408549],
  [1149.584399, 1151.122585],
  [1161.473175, 1163.540522],
  [1165.132336, 1166.653673],
  [1168.066667, 1169.743605],
  [1184.205465, 1185.725782],
  [1191.027007, 1192.272948],
  [1196.527755, 1197.885782],
  [1208.429297, 1210.594762],
  [1210.643424, 1213.003469],
  [1213.181474, 1216.070748],
  [1218.263968, 1219.845011],
  [1223.169297, 1224.008685],
  [1225.470748, 1226.80458],
  [1228.385782, 1230.084286],
  [1232.837324, 1235.158118],
  [1247.323061, 1248.775102],
  [1253.780612, 1254.724785],
  [1256.218005, 1257.577166],
  [1260.762313, 1261.975873],
  [1262.198594, 1264.217324],
  [1285.493061, 1286.423515],
  [1289.111927, 1290.336871],
  [1290.40542, 1291.465125],
  [1293.634014, 1295.888912],
  [1296.223175, 1297.759002],
  [1299.520952, 1300.401587],
  [1307.169206, 1308.3],
  [1314.068163, 1314.971224],
  [1319.861134, 1320.769728],
  [1325.597188, 1326.603787],
  [1328.272426, 1329.363175],
  [1329.36322, 1331.302834],
  [1334.894649, 1336.777483],
  [1344.627982, 1345.567234],
  [1347.73746, 1348.555329],
  [1355.641746, 1356.776168],
  [1357.727052, 1358.656213],
  [1358.660771, 1359.574558],
  [1374.003447, 1379.738254],
  [1380.690567, 1383.225873],
  [1383.750363, 1385.551905],
  [1388.481995, 1389.300113],
  [1403.513537, 1404.395329],
  [1404.617846, 1405.895828],
  [1417.486712, 1418.846599],
  [1421.092653, 1422.239501],
  [1425.748299, 1426.550522],
  [1429.819796, 1430.840567],
  [1436.173265, 1437.049184],
  [1440.065556, 1441.281111],
  [1441.514626, 1443.573991],
  [1447.880998, 1450.299569],
  [1457.364127, 1458.40907],
  [1459.141995, 1460.13102],
  [1482.065601, 1483.079751],
  [1515.450544, 1516.251179],
  [1522.096916, 1523.492925],
  [1533.429297, 1534.45068],
  [1543.062902, 1543.991134],
  [1551.80059, 1552.967188],
  [1565.880998, 1566.779637],
  [1567.7422, 1568.905941],
  [1570.882698, 1572.082109],
  [1572.786349, 1573.991134],
  [1581.19263, 1582.485714],
  [1593.639093, 1596.00263],
  [1597.122086, 1598.600408],
  [1603.827347, 1604.722472],
  [1605.913039, 1606.722857],
  [1614.615646, 1616.187483],
  [1618.391338, 1620.307188],
  [1622.481723, 1623.346757],
  [1623.804603, 1624.970816],
  [1626.436961, 1627.575125],
  [1628.430952, 1629.569546],
  [1632.898231, 1634.008685],
  [1643.645556, 1645.182766],
  [1660.386213, 1661.28898],
  [1678.759637, 1679.972494],
  [1680.351769, 1681.62356],
  [1693.969274, 1695.513061],
  [1704.177687, 1705.175329],
  [1713.308798, 1714.668345],
  [1718.639501, 1719.853061],
  [1739.133424, 1739.963537],
  [1740.913061, 1741.810771],
  [1742.181179, 1743.910567],
  [1745.713583, 1746.791973],
  [1748.065306, 1748.939456],
  [1759.796757, 1763.161497],
  [1763.985465, 1765.70585],
  [1766.685147, 1768.033039],
  [1768.64263, 1770.62941],
  [1778.234082, 1779.674535],
  [1783.531134, 1784.629342],
  [1789.145442, 1790.210794],
  [1791.136621, 1793.451519],
  [1794.577143, 1795.639524],
  [1796.890091, 1798.091315],
  [1817.663741, 1821.196054],
  [1823.200317, 1824.243152],
  [1828.572948, 1830.06458],
  [1837.696054, 1839.271179],
  [1844.604921, 1845.594966],
  [1847.55068, 1848.8361],
  [1857.450408, 1861.085147],
  [1862.182449, 1864.631769],
  [1870.93424, 1874.323968],
  [1876.281882, 1877.094263],
  [1880.32839, 1882.271905],
  [1882.807324, 1884.817574],
  [1888.681859, 1889.509206],
  [1889.788707, 1891.221429],
  [1908.780068, 1910.439819],
  [1911.164694, 1912.630499],
  [1914.445283, 1916.546825],
  [1918.383243, 1919.796871],
  [1920.773152, 1922.352154],
  [1929.470249, 1930.731406],
  [1931.253424, 1932.279819],
  [1937.872789, 1938.884989],
  [1959.471701, 1960.640907],
  [1965.351973, 1968.273311],
  [1970.599025, 1971.820884],
  [1972.876984, 1974.078844],
  [1990.638594, 1991.708481],
  [1994.42059, 1995.246395],
  [1996.066893, 1997.623696],
  [2000.108526, 2001.127528],
  [2001.143991, 2002.159252],
  [2002.345079, 2003.490658],
  [2003.546893, 2005.201111],
  [2007.713696, 2008.858299],
  [2009.461497, 2010.44712],
  [2011.001134, 2012.6922],
  [2020.77, 2021.616848],
  [2025.400726, 2028.159048],
  [2031.690136, 2032.545147],
  [2049.676667, 2052.313016],
  [2064.557415, 2065.52932],
  [2078.981224, 2080.606417],
  [2084.458549, 2085.273764],
  [2101.928027, 2103.399524],
  [2106.054218, 2106.881179],
  [2117.789116, 2118.985238],
  [2121.505193, 2122.503515],
  [2134.729728, 2135.64932],
  [2135.840544, 2137.346667],
  [2142.444943, 2143.492608],
  [2149.284286, 2150.512494],
  [2155.659002, 2156.63288],
  [2163.522494, 2164.616281],
  [2164.883447, 2166.059887],
  [2166.838095, 2168.281066],
  [2174.863243, 2176.52254],
  [2180.084943, 2181.183492],
  [2184.884286, 2186.171791],
  [2188.168073, 2189.180499],
  [2189.193651, 2190.776599],
  [2204.987982, 2208.874717],
  [2211.526735, 2214.111837],
  [2216.137007, 2217.521905],
  [2229.979093, 2231.214082],
  [2232.08932, 2233.005465],
  [2242.698912, 2243.642698],
  [2251.31127, 2252.292766],
  [2255.455714, 2256.78127],
  [2270.146417, 2271.787596],
  [2274.070068, 2275.128844],
  [2280.683583, 2281.58381],
  [2284.256576, 2285.730771],
  [2288.650544, 2291.446327],
  [2307.863991, 2309.08805],
  [2309.821927, 2311.145238],
  [2313.27093, 2314.202857],
  [2319.131179, 2320.157868],
  [2321.610363, 2322.700952],
  [2344.905397, 2345.800726],
  [2345.884535, 2348.016689],
  [2349.022245, 2349.878458],
  [2364.128685, 2365.391315],
  [2369.114717, 2370.133696],
  [2380.040862, 2381.668413],
  [2388.287347, 2389.439977],
  [2402.180385, 2403.337075],
  [2403.35, 2404.429955],
  [2430.309048, 2432.252676],
  [2435.944082, 2437.761565],
  [2449.81034, 2450.635896],
  [2454.812426, 2455.84932],
  [2457.59585, 2458.625125],
  [2460.633424, 2462.0139],
  [2468.521995, 2469.650567],
  [2478.685306, 2479.68195],
  [2480.531202, 2482.945737],
  [2486.458753, 2487.348277],
  [2490.32941, 2492.3278],
  [2502.472653, 2503.869909],
  [2509.612313, 2510.425057],
  [2515.787868, 2516.624603],
  [2525.374853, 2526.458186],
  [2535.496168, 2537.657664],
  [2538.147959, 2539.103673],
  [2542.825533, 2543.841633],
  [2549.760862, 2550.667868],
  [2601.505828, 2602.318707],
  [2603.217483, 2604.061088],
  [2608.312721, 2609.164286],
  [2610.39356, 2611.294649],
  [2673.947098, 2674.86102],
  [2689.85288, 2690.685624],
  [2700.974807, 2701.922404],
  [2703.090159, 2703.965283],
  [2707.233333, 2708.271927],
  [2724.35542, 2725.219955],
  [2733.836349, 2735.068594],
  [2739.717664, 2740.626372],
  [2744.172336, 2745.025057],
  [2746.255669, 2747.163039],
  [2755.302925, 2756.778844],
  [2765.414785, 2766.391678],
  [2779.94737, 2781.597937],
  [2782.044966, 2784.167528],
  [2785.693537, 2787.089887],
  [2788.19941, 2789.279569],
  [2796.736327, 2798.255692],
  [2801.533673, 2802.840408],
  [2810.734331, 2812.022744],
  [2821.2, 2822.062971],
  [2823.31644, 2824.677551],
  [2825.807392, 2826.855714],
  [2831.732268, 2832.843923],
  [2840.231678, 2841.291542],
  [2841.568844, 2842.596349],
  [2848.199864, 2849.157868],
  [2849.3778, 2850.338617],
  [2855.038844, 2856.100884],
  [2871.376599, 2874.636281],
  [2875.036984, 2876.366508],
  [2887.069342, 2887.878549],
  [2893.390113, 2894.509864],
  [2907.554535, 2908.368934],
  [2925.721338, 2926.540023],
  [2926.554354, 2928.559048],
  [2930.071723, 2931.24229],
  [2937.907574, 2938.919501],
  [2941.89678, 2942.768095],
  [2944.372041, 2945.71712],
  [2947.199206, 2948.473265],
  [2949.755397, 2950.739388],
  [2955.795624, 2956.689025],
  [2958.956145, 2959.840658],
  [2979.250794, 2980.099116],
  [2980.93288, 2982.214059],
  [2982.928367, 2984.102086],
  [3005.736803, 3006.706984],
  [3007.74424, 3009.916349],
  [3010.274422, 3011.340431],
  [3013.532404, 3015.662948],
  [3016.377551, 3018.296576],
  [3025.65932, 3026.60551],
  [3026.914898, 3028.165692],
  [3036.743356, 3039.454399],
  [3040.58034, 3041.408277],
  [3043.329456, 3044.14941],
  [3048.251066, 3049.155601],
  [3052.395986, 3053.202834],
  [3063.632132, 3064.653764],
  [3064.68873, 3066.348141],
  [3066.362925, 3067.645692],
  [3069.062381, 3071.861383],
  [3074.70229, 3076.464558],
  [3078.357211, 3079.516553],
  [3081.263356, 3082.579342],
  [3088.360408, 3089.532653],
  [3092.85059, 3094.504422],
  [3095.393197, 3096.53966],
  [3099.145918, 3100.855238],
  [3101.075306, 3103.759025],
  [3104.156122, 3104.959456],
  [3106.924444, 3107.826032],
  [3132.890748, 3134.368798],
];

const TOTAL_SILENCE_S = Math.round(SILENCE.reduce((a, [s, e]) => a + (e - s), 0));
const SILENCE_PCT = ((TOTAL_SILENCE_S / VIDEO_DURATION) * 100).toFixed(1);

// ── Option A – Pre-emptive Hard Skip ─────────────────────────────────────────
// YouTube iframe seek takes ~150-250ms to complete. By triggering LEAD_SECS
// before each silence, the seek lands right as silence begins → zero audible gap.
const LEAD_SECS = 0.35;

function OptionA() {
  const playerRef = useRef<any>(null);
  const [playing, setPlaying] = useState(false);
  const [saved, setSaved] = useState(0);
  const [skips, setSkips] = useState(0);
  const [inSilence, setInSilence] = useState(false);
  const lockRef = useRef(false);
  // Track last seek destination so we never re-trigger the same silence
  const lastLandRef = useRef(-1);

  function handleProgress({ playedSeconds }: { playedSeconds: number }) {
    if (lockRef.current) return;
    // Pre-emptive: detect silence LEAD_SECS before it starts, and skip
    // silences we haven't seeked past yet.
    const seg = SILENCE.find(([s, e]) =>
      playedSeconds >= s - LEAD_SECS &&
      playedSeconds < e &&
      e > lastLandRef.current
    );
    setInSilence(!!seg && playedSeconds >= (seg?.[0] ?? Infinity));
    if (!seg || !playerRef.current) return;

    lockRef.current = true;

    // Chain consecutive silences into a single seek — handles clusters
    // like [1357.73,1358.66]→[1358.66,1359.57] with only a 4ms gap.
    let landAt = seg[1] + 0.1;
    let totalSaved = seg[1] - seg[0]; // full silence duration
    let totalSkips = 1;
    let cursor: [number, number] = seg;
    let next = SILENCE.find(([s]) => s > cursor[1] && s <= landAt + 2.0);
    while (next) {
      totalSaved += next[1] - next[0];
      landAt = next[1] + 0.1;
      totalSkips++;
      cursor = next;
      next = SILENCE.find(([s]) => s > cursor[1] && s <= landAt + 2.0);
    }

    lastLandRef.current = landAt;
    setSaved((v) => parseFloat((v + totalSaved).toFixed(1)));
    setSkips((v) => v + totalSkips);
    playerRef.current.seekTo(landAt, "seconds");
    setTimeout(() => { lockRef.current = false; }, 250);
  }

  function handleUserSeek() {
    // Reset on manual seek so we re-detect from the new position
    if (lockRef.current) return; // ignore our own programmatic seeks
    lastLandRef.current = -1;
  }

  return (
    <OptionCard
      letter="A"
      icon={<SkipForward className="h-5 w-5" />}
      title="Hard Skip"
      description={`Seek fires ${LEAD_SECS}s before each silence — YouTube finishes seeking right as silence begins, giving near-zero audible gap. Chains consecutive clusters into one jump.`}
      accentColor="text-blue-400"
      badgeColor="bg-blue-500/20 border-blue-500/30"
      stats={[
        { label: "Time saved", value: `${saved.toFixed(1)}s` },
        { label: "Skips made", value: skips },
        { label: "Status", value: inSilence ? "⏩ jumping…" : "▶ playing" },
      ]}
    >
      <ReactPlayer
        ref={playerRef}
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        onProgress={handleProgress}
        onSeek={handleUserSeek}
        progressInterval={100}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
    </OptionCard>
  );
}

// ── Option C – Speed Ramp (scheduled timer, no polling) ──────────────────────
// Uses setTimeout instead of onProgress so timing is exact.
// speedUp timer fires at silence start → 5×. slowDown timer fires
// fastDuration/RAMP_SPEED wall-seconds later → 1×. No polling overhead.
const RAMP_SPEED = 5;
const RAMP_EXIT_EARLY = 0.4; // restore 1× this many video-secs before silence ends

function OptionC() {
  const playerRef = useRef<any>(null);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [inSilence, setInSilence] = useState(false);
  const [savedApprox, setSavedApprox] = useState(0);
  const speedUpRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const slowDownRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playingRef = useRef(false);
  const seekingRef = useRef(false);

  function clearTimers() {
    if (speedUpRef.current) { clearTimeout(speedUpRef.current); speedUpRef.current = null; }
    if (slowDownRef.current) { clearTimeout(slowDownRef.current); slowDownRef.current = null; }
  }

  function scheduleFrom(fromSecs: number) {
    clearTimers();
    const seg = SILENCE.find(([s]) => s > fromSecs + 0.05);
    if (!seg || !playingRef.current) return;
    const [start, end] = seg;
    // Video-seconds of silence that will play at RAMP_SPEED×
    const fastVideoSecs = Math.max(0, end - RAMP_EXIT_EARLY - start);

    speedUpRef.current = setTimeout(() => {
      if (!playingRef.current) return;
      if (fastVideoSecs < 0.1) {
        // Silence too short to ramp — advance scheduling to next segment
        scheduleFrom(end);
        return;
      }
      setSpeed(RAMP_SPEED);
      setInSilence(true);
      // At RAMP_SPEED×, fastVideoSecs of video passes in fastVideoSecs/RAMP_SPEED wall-secs
      slowDownRef.current = setTimeout(() => {
        setSpeed(1);
        setInSilence(false);
        setSavedApprox((v) =>
          parseFloat((v + fastVideoSecs * (1 - 1 / RAMP_SPEED)).toFixed(1))
        );
        // Video is now at end - RAMP_EXIT_EARLY; schedule next silence from there
        scheduleFrom(end - RAMP_EXIT_EARLY);
      }, Math.max(20, (fastVideoSecs / RAMP_SPEED) * 1000));
    }, Math.max(20, (start - fromSecs) * 1000));
  }

  function handlePlay() {
    playingRef.current = true;
    setPlaying(true);
    scheduleFrom(playerRef.current?.getCurrentTime?.() ?? 0);
  }

  function handlePause() {
    playingRef.current = false;
    setPlaying(false);
    setSpeed(1);
    setInSilence(false);
    clearTimers();
  }

  function handleSeek(secs: number) {
    if (seekingRef.current) return;
    setSpeed(1);
    setInSilence(false);
    if (playingRef.current) scheduleFrom(secs);
  }

  useEffect(() => () => clearTimers(), []);

  return (
    <OptionCard
      letter="C"
      icon={<Gauge className="h-5 w-5" />}
      title="Speed Ramp"
      description={`Silences play at ${RAMP_SPEED}× — no hard cut, sounds natural. Scheduled timer fires at each silence start (zero polling), restores 1× speed ${RAMP_EXIT_EARLY}s before speech resumes.`}
      accentColor="text-amber-400"
      badgeColor="bg-amber-500/20 border-amber-500/30"
      stats={[
        { label: "Current speed", value: `${speed}×` },
        { label: "Wall-time saved ≈", value: `${savedApprox.toFixed(1)}s` },
        { label: "Status", value: inSilence ? `🚀 ${speed}× speed` : "▶ 1× normal" },
      ]}
    >
      <ReactPlayer
        ref={playerRef}
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        playbackRate={speed}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        onPlay={handlePlay}
        onPause={handlePause}
        onSeek={handleSeek}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
    </OptionCard>
  );
}

// ── Option D – Scheduled Skip (setTimeout) ────────────────────────────────────
function OptionD() {
  const playerRef = useRef<any>(null);
  const [playing, setPlaying] = useState(false);
  const [skips, setSkips] = useState(0);
  const [saved, setSaved] = useState(0);
  const [nextSkipLabel, setNextSkipLabel] = useState<string>("—");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const playingRef = useRef(false);
  const seekingRef = useRef(false);

  function clearTimer() {
    if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null; }
    setNextSkipLabel("—");
  }

  // Pre-emptive: fire LEAD_MS before silence starts so YouTube finishes
  // seeking right as silence begins — giving near-zero audible gap.
  const LEAD_MS = 350;

  function scheduleNextFrom(fromSeconds: number) {
    clearTimer();
    const seg = SILENCE.find(([s]) => s > fromSeconds + 0.05);
    if (!seg) return;
    const [start, end] = seg;
    const delaySecs = start - fromSeconds;
    const mm = Math.floor(start / 60).toString().padStart(2, "0");
    const ss = Math.floor(start % 60).toString().padStart(2, "0");
    setNextSkipLabel(`${mm}:${ss}`);
    // Fire LEAD_MS early so seek completes right as silence starts
    timerRef.current = setTimeout(() => {
      if (!playingRef.current || !playerRef.current) return;
      const currentTime = playerRef.current.getCurrentTime?.() ?? 0;
      if (Math.abs(currentTime - start) > 15) {
        scheduleNextFrom(currentTime);
        return;
      }
      seekingRef.current = true;
      setSaved((v) => parseFloat((v + (end - start)).toFixed(1)));
      setSkips((v) => v + 1);
      playerRef.current.seekTo(end + 0.1, "seconds");
      setTimeout(() => {
        seekingRef.current = false;
        scheduleNextFrom(end + 0.1);
      }, 200);
    }, Math.max(20, delaySecs * 1000 - LEAD_MS));
  }

  function handlePlay() {
    playingRef.current = true;
    setPlaying(true);
    const cur = playerRef.current?.getCurrentTime?.() ?? 0;
    scheduleNextFrom(cur);
  }

  function handlePause() {
    playingRef.current = false;
    setPlaying(false);
    clearTimer();
  }

  function handleSeek(seconds: number) {
    // Ignore seeks we triggered ourselves
    if (seekingRef.current) return;
    if (playingRef.current) scheduleNextFrom(seconds);
  }

  useEffect(() => () => clearTimer(), []);

  return (
    <OptionCard
      letter="D"
      icon={<Clock className="h-5 w-5" />}
      title="Scheduled Skip"
      description="Pre-computed timestamps become JS setTimeout calls. One timer at a time — fires at the silence start, seeks to its end, then queues the next. Zero polling overhead."
      accentColor="text-emerald-400"
      badgeColor="bg-emerald-500/20 border-emerald-500/30"
      stats={[
        { label: "Skips made", value: skips },
        { label: "Time saved", value: `${saved.toFixed(1)}s` },
        { label: "Next skip at", value: nextSkipLabel },
      ]}
    >
      <ReactPlayer
        ref={playerRef}
        url={VIDEO_URL}
        width="100%"
        height="100%"
        style={{ aspectRatio: "16/9" }}
        controls
        playing={playing}
        light={!playing && POSTER}
        onClickPreview={() => setPlaying(true)}
        onPlay={handlePlay}
        onPause={handlePause}
        onSeek={handleSeek}
        config={{ playerVars: { modestbranding: 1, rel: 0 } } as any}
      />
    </OptionCard>
  );
}

// ── Shared card wrapper ────────────────────────────────────────────────────────
interface StatItem {
  label: string;
  value: string | number;
}

interface OptionCardProps {
  letter: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  accentColor: string;
  badgeColor: string;
  stats: StatItem[];
  children: React.ReactNode;
}

function OptionCard({
  letter,
  icon,
  title,
  description,
  accentColor,
  badgeColor,
  stats,
  children,
}: OptionCardProps) {
  return (
    <div className="rounded-xl border border-white/10 overflow-hidden bg-card">
      {/* Header */}
      <div className="flex items-start gap-4 p-5 border-b border-white/10 bg-white/5">
        <div className={cn("flex items-center justify-center w-10 h-10 rounded-lg border font-bold text-lg shrink-0", badgeColor, accentColor)}>
          {letter}
        </div>
        <div className="flex-1 min-w-0">
          <div className={cn("flex items-center gap-2 font-semibold text-base", accentColor)}>
            {icon}
            Option {letter} — {title}
          </div>
          <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{description}</p>
        </div>
      </div>

      {/* Player + stats */}
      <div className="p-5 space-y-4">
        {/* Live stats */}
        <div className="grid grid-cols-3 gap-3">
          {stats.map((s) => (
            <div key={s.label} className="rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-center">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className={cn("text-sm font-semibold mt-0.5 tabular-nums", accentColor)}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Video */}
        <div className="rounded-xl overflow-hidden bg-black border border-white/10">
          {children}
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "A", label: "Option A — Hard Skip" },
  { id: "C", label: "Option C — Speed Ramp" },
  { id: "D", label: "Option D — Scheduled Skip" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SilenceTestPage() {
  const [activeTab, setActiveTab] = useState<TabId>("A");

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Silence Removal — Test Lab</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Three universally-compatible approaches — iOS, Android, desktop web — tested on:{" "}
          <span className="text-white/80 font-medium">18.065 — Lecture 1: The Column Space of A</span>
          {" "}(YiqIkSHSmyc)
        </p>
      </div>

      {/* Analysis summary */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="flex items-center gap-2 text-sm font-medium mb-3">
          <Info className="h-4 w-4 text-primary" />
          FFmpeg silencedetect analysis — <code className="text-xs bg-white/10 px-1.5 py-0.5 rounded">-40dB threshold, 0.8s min duration</code>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Video length", value: "52m 14s" },
            { label: "Silent segments", value: `${SILENCE.length}` },
            { label: "Total silence", value: `${TOTAL_SILENCE_S}s` },
            { label: "% silent", value: `${SILENCE_PCT}%` },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-lg font-bold text-primary mt-0.5">{s.value}</p>
            </div>
          ))}
        </div>
        <details className="mt-3">
          <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground select-none">
            Show all {SILENCE.length} silent segments
          </summary>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {SILENCE.map(([s, e], i) => (
              <span key={i} className="text-xs bg-white/10 rounded px-2 py-0.5 font-mono">
                {s.toFixed(1)}s → {e.toFixed(1)}s ({(e - s).toFixed(1)}s)
              </span>
            ))}
          </div>
        </details>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 border border-white/10 rounded-lg p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-white/10"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active panel */}
      {activeTab === "A" && <OptionA />}
      {activeTab === "C" && <OptionC />}
      {activeTab === "D" && <OptionD />}

      {/* Bottom note */}
      <div className="rounded-lg border border-white/10 bg-white/5 p-4 text-xs text-muted-foreground space-y-1">
        <p><span className="text-white/60 font-medium">Option A — Hard Skip</span> — Best for eliminating dead air completely. Jumps to end of each silence in one seek call. Chains consecutive clusters in a single jump. Works on iOS, Android, desktop.</p>
        <p><span className="text-white/60 font-medium">Option C — Speed Ramp</span> — Silences play at 5× instead of being cut. Feels more natural. Restores 1× speed slightly before speech resumes to avoid clipping first words. Works on iOS, Android, desktop via YouTube iframe API.</p>
        <p><span className="text-white/60 font-medium">Option D — Scheduled Skip</span> — No polling. One JS timer queued at a time, fires at the next silence start, seeks to its end, then schedules the next. Zero CPU overhead during speech. Works on iOS, Android, desktop.</p>
      </div>
    </div>
  );
}
