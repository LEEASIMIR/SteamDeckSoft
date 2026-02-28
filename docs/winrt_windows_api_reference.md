# winrt-Windows API 카테고리 레퍼런스

Python에서 `winrt-Windows.*` 패키지로 사용 가능한 Windows Runtime API 목록.
설치: `pip install winrt-Windows.{카테고리}`

> 기본 의존성: `winrt-runtime`, `winrt-Windows.Foundation`

---

## Foundation — 핵심 기반

| 패키지 | 설명 |
|---|---|
| `Windows.Foundation` | 비동기 작업, URI, DateTime 등 WinRT 기본 타입 |
| `Windows.Foundation.Collections` | IVector, IMap 등 WinRT 컬렉션 인터페이스 |
| `Windows.Foundation.Diagnostics` | ETW 로깅 및 진단 채널 |
| `Windows.Foundation.Metadata` | API 계약, 특성 메타데이터 |
| `Windows.Foundation.Numerics` | 벡터, 행렬, 쿼터니언 수학 타입 |

---

## AI — 인공지능

| 패키지 | 설명 |
|---|---|
| `Windows.AI.Actions` | AI 액션 프레임워크 |
| `Windows.AI.Actions.Hosting` | AI 액션 호스팅 |
| `Windows.AI.Actions.Provider` | AI 액션 제공자 |
| `Windows.AI.MachineLearning` | Windows ML — ONNX 모델 추론 (GPU/CPU) |
| `Windows.AI.MachineLearning.Preview` | ML 미리보기 API |
| `Windows.AI.ModelContextProtocol` | MCP (Model Context Protocol) 지원 |

---

## Media — 미디어

| 패키지 | 설명 |
|---|---|
| `Windows.Media` | 미디어 기본 타입 및 마커 |
| `Windows.Media.Audio` | 오디오 그래프 (믹싱, 이펙트, 입출력) |
| `Windows.Media.AppBroadcasting` | 앱 방송 (스트리밍) |
| `Windows.Media.AppRecording` | 앱 화면 녹화 |
| `Windows.Media.Capture` | 카메라/마이크 캡처 |
| `Windows.Media.Capture.Core` | 캡처 코어 |
| `Windows.Media.Capture.Frames` | 카메라 프레임 리더 (실시간 프레임 접근) |
| `Windows.Media.Casting` | 미디어 캐스팅 (Miracast 등) |
| `Windows.Media.ClosedCaptioning` | 자막 설정 접근 |
| `Windows.Media.ContentRestrictions` | 콘텐츠 연령 제한 |
| **`Windows.Media.Control`** | **SMTC — 시스템 미디어 재생 상태 감지/제어** |
| `Windows.Media.Core` | MediaSource, 타임라인 마커 |
| `Windows.Media.Core.Preview` | 미디어 코어 미리보기 |
| `Windows.Media.Devices` | 오디오/비디오 장치 설정 |
| `Windows.Media.Devices.Core` | 카메라 내부 파라미터 |
| `Windows.Media.DialProtocol` | DIAL 프로토콜 (TV 캐스팅) |
| `Windows.Media.Editing` | 비디오 편집 (합성, 트리밍) |
| `Windows.Media.Effects` | 오디오/비디오 이펙트 |
| `Windows.Media.FaceAnalysis` | 얼굴 감지 |
| `Windows.Media.Import` | 미디어 가져오기 (카메라, SD카드) |
| `Windows.Media.MediaProperties` | 인코딩 프로필 (H.264, AAC 등) |
| `Windows.Media.Miracast` | Miracast 무선 디스플레이 |
| `Windows.Media.Ocr` | 이미지에서 텍스트 인식 (OCR) |
| `Windows.Media.PlayTo` | Play To 미디어 스트리밍 |
| `Windows.Media.Playback` | MediaPlayer, 재생 목록 |
| `Windows.Media.Playlists` | 재생 목록 파일 관리 |
| `Windows.Media.Protection` | DRM 콘텐츠 보호 |
| `Windows.Media.Protection.PlayReady` | PlayReady DRM |
| `Windows.Media.Render` | 오디오 렌더링 카테고리 |
| `Windows.Media.SpeechRecognition` | 음성 인식 (STT) |
| `Windows.Media.SpeechSynthesis` | 음성 합성 (TTS) |
| `Windows.Media.Streaming.Adaptive` | 적응형 스트리밍 (HLS, DASH) |
| `Windows.Media.Transcoding` | 미디어 트랜스코딩 |

---

## Devices — 하드웨어 장치

| 패키지 | 설명 |
|---|---|
| `Windows.Devices` | 장치 기본 타입 |
| `Windows.Devices.Adc` | ADC (아날로그-디지털 변환기) |
| `Windows.Devices.Bluetooth` | 블루투스 장치 통신 |
| `Windows.Devices.Bluetooth.Advertisement` | BLE 광고 패킷 스캔/송출 |
| `Windows.Devices.Bluetooth.GenericAttributeProfile` | BLE GATT 프로필 |
| `Windows.Devices.Bluetooth.Rfcomm` | 블루투스 RFCOMM 통신 |
| `Windows.Devices.Display` | 디스플레이 정보 |
| `Windows.Devices.Display.Core` | 디스플레이 코어 (모드 설정) |
| `Windows.Devices.Enumeration` | 장치 열거 및 감시 |
| `Windows.Devices.Geolocation` | GPS/위치 서비스 |
| `Windows.Devices.Geolocation.Geofencing` | 지오펜싱 (위치 기반 트리거) |
| `Windows.Devices.Gpio` | GPIO 핀 제어 (IoT) |
| `Windows.Devices.Haptics` | 햅틱 피드백 (진동) |
| `Windows.Devices.HumanInterfaceDevice` | HID 장치 접근 |
| `Windows.Devices.I2c` | I2C 버스 통신 (IoT) |
| `Windows.Devices.Input` | 입력 장치 정보 (터치, 펜) |
| `Windows.Devices.Lights` | LED 조명 제어 |
| `Windows.Devices.Lights.Effects` | LED 이펙트 (파동, 깜빡임) |
| `Windows.Devices.Midi` | MIDI 입출력 |
| `Windows.Devices.PointOfService` | POS 장치 (바코드, 영수증 프린터) |
| `Windows.Devices.Portable` | 휴대용 장치 (MTP) |
| `Windows.Devices.Power` | 배터리 정보 |
| `Windows.Devices.Printers` | 프린터 정보 및 제어 |
| `Windows.Devices.Pwm` | PWM 신호 출력 (IoT) |
| `Windows.Devices.Radios` | 무선 라디오 on/off (Wi-Fi, BT, NFC) |
| `Windows.Devices.Scanners` | 스캐너 장치 |
| `Windows.Devices.Sensors` | 가속도계, 자이로, 조도, 나침반 등 센서 |
| `Windows.Devices.SerialCommunication` | 시리얼 포트 (COM) 통신 |
| `Windows.Devices.SmartCards` | 스마트카드 리더 |
| `Windows.Devices.Sms` | SMS 메시지 (모바일) |
| `Windows.Devices.Spi` | SPI 버스 통신 (IoT) |
| `Windows.Devices.Usb` | USB 장치 접근 |
| `Windows.Devices.WiFi` | Wi-Fi 네트워크 스캔/연결 |
| `Windows.Devices.WiFiDirect` | Wi-Fi Direct P2P 연결 |

---

## Networking — 네트워크

| 패키지 | 설명 |
|---|---|
| `Windows.Networking` | 호스트네임, 엔드포인트 기본 타입 |
| `Windows.Networking.BackgroundTransfer` | 백그라운드 다운로드/업로드 |
| `Windows.Networking.Connectivity` | 네트워크 상태, 연결 프로필 |
| `Windows.Networking.NetworkOperators` | 모바일 네트워크 사업자 |
| `Windows.Networking.Proximity` | NFC, 근접 통신 |
| `Windows.Networking.PushNotifications` | WNS 푸시 알림 |
| `Windows.Networking.ServiceDiscovery.Dnssd` | DNS-SD 서비스 검색 |
| `Windows.Networking.Sockets` | TCP/UDP/WebSocket 소켓 |
| `Windows.Networking.Vpn` | VPN 플러그인 |
| `Windows.Networking.XboxLive` | Xbox Live 네트워킹 |

---

## Storage — 파일 및 저장소

| 패키지 | 설명 |
|---|---|
| `Windows.Storage` | 파일/폴더 접근 (StorageFile, StorageFolder) |
| `Windows.Storage.AccessCache` | 최근 사용 파일/폴더 캐시 |
| `Windows.Storage.BulkAccess` | 대량 파일 속성 조회 |
| `Windows.Storage.Compression` | 압축/해제 스트림 |
| `Windows.Storage.FileProperties` | 파일 속성 (썸네일, 메타데이터) |
| `Windows.Storage.Pickers` | 파일/폴더 선택 다이얼로그 |
| `Windows.Storage.Provider` | 클라우드 동기화 엔진 |
| `Windows.Storage.Search` | 파일 검색 쿼리 |
| `Windows.Storage.Streams` | IRandomAccessStream, Buffer 등 스트림 IO |

---

## UI — 사용자 인터페이스

| 패키지 | 설명 |
|---|---|
| `Windows.UI` | Color 등 기본 UI 타입 |
| `Windows.UI.Accessibility` | 접근성 설정 |
| `Windows.UI.Composition` | Visual Layer 합성 (애니메이션, 이펙트) |
| `Windows.UI.Composition.Desktop` | 데스크톱 윈도우 합성 |
| `Windows.UI.Composition.Effects` | 시각 효과 (블러, 그림자) |
| `Windows.UI.Composition.Interactions` | 관성 스크롤, 제스처 |
| `Windows.UI.Core` | CoreWindow, 디스패처 |
| `Windows.UI.Input` | 포인터, 제스처, 크로스슬라이드 |
| `Windows.UI.Input.Inking` | 디지털 잉크 (펜 입력) |
| `Windows.UI.Input.Inking.Analysis` | 잉크 필기 인식 |
| `Windows.UI.Input.Preview.Injection` | 입력 시뮬레이션 (터치, 마우스 주입) |
| `Windows.UI.Input.Spatial` | 공간 입력 (MR 컨트롤러) |
| `Windows.UI.Notifications` | 토스트/타일 알림 |
| `Windows.UI.Notifications.Management` | 알림 리스너 (알림 센터 읽기) |
| `Windows.UI.Popups` | 메시지 다이얼로그 |
| `Windows.UI.Shell` | 작업 표시줄, 핀 고정 |
| `Windows.UI.StartScreen` | 시작 메뉴 타일 |
| `Windows.UI.Text` | 서식 텍스트 |
| `Windows.UI.ViewManagement` | 앱 뷰, 상태 표시줄, UISettings |
| `Windows.UI.WindowManagement` | 앱 창 관리 (다중 창) |

---

## Graphics — 그래픽

| 패키지 | 설명 |
|---|---|
| `Windows.Graphics` | 기본 그래픽 타입 (SizeInt32 등) |
| `Windows.Graphics.Capture` | 화면/창 캡처 (스크린샷, 녹화) |
| `Windows.Graphics.DirectX` | DirectX 픽셀 포맷 |
| `Windows.Graphics.DirectX.Direct3D11` | Direct3D 11 상호운용 |
| `Windows.Graphics.Display` | 디스플레이 DPI, 색영역, HDR |
| `Windows.Graphics.Holographic` | 홀로그래픽 렌더링 (MR) |
| `Windows.Graphics.Imaging` | 이미지 디코딩/인코딩 (BitmapDecoder) |
| `Windows.Graphics.Printing` | 인쇄 |
| `Windows.Graphics.Printing3D` | 3D 프린팅 (3MF) |

---

## System — 시스템

| 패키지 | 설명 |
|---|---|
| `Windows.System` | 앱 실행 (LauncherOptions), 메모리 관리 |
| `Windows.System.Diagnostics` | 프로세스 진단, 시스템 정보 |
| `Windows.System.Diagnostics.DevicePortal` | Device Portal API |
| `Windows.System.Diagnostics.Telemetry` | 텔레메트리 |
| `Windows.System.Display` | 화면 켜짐 유지 (DisplayRequest) |
| `Windows.System.Inventory` | 설치된 앱 목록 |
| `Windows.System.Power` | 전원 상태, 배터리 세이버 |
| `Windows.System.Profile` | 장치/시스템 프로필 정보 |
| `Windows.System.RemoteDesktop` | 원격 데스크톱 세션 |
| `Windows.System.RemoteSystems` | 원격 장치 검색 및 연결 |
| `Windows.System.Threading` | 스레드 풀 |
| `Windows.System.Update` | 시스템 업데이트 관리 |
| `Windows.System.UserProfile` | 사용자 프로필 (잠금 화면, 계정 사진) |

---

## Security — 보안

| 패키지 | 설명 |
|---|---|
| `Windows.Security.Authentication.Web` | OAuth 웹 인증 브로커 |
| `Windows.Security.Authentication.Web.Core` | 웹 계정 관리자 (Microsoft 계정) |
| `Windows.Security.Authentication.OnlineId` | 온라인 ID 인증 |
| `Windows.Security.Authorization.AppCapabilityAccess` | 앱 권한 확인 (카메라, 위치 등) |
| `Windows.Security.Credentials` | 자격 증명 보관소 (PasswordVault) |
| `Windows.Security.Credentials.UI` | Windows Hello, PIN 프롬프트 |
| `Windows.Security.Cryptography` | 랜덤 버퍼, Base64, Hex 변환 |
| `Windows.Security.Cryptography.Certificates` | 인증서 관리 |
| `Windows.Security.Cryptography.Core` | 해시, 암호화, 서명 (AES, RSA, SHA) |
| `Windows.Security.Cryptography.DataProtection` | 데이터 보호 (DPAPI) |
| `Windows.Security.DataProtection` | 데이터 보호 관리자 |

---

## Data — 데이터 처리

| 패키지 | 설명 |
|---|---|
| `Windows.Data.Html` | HTML → 텍스트 변환 |
| `Windows.Data.Json` | JSON 파서 (JsonObject, JsonArray) |
| `Windows.Data.Pdf` | PDF 렌더링 (페이지 → 이미지) |
| `Windows.Data.Text` | 텍스트 분할, 유니코드, 음역 |
| `Windows.Data.Xml.Dom` | XML DOM 파서 |
| `Windows.Data.Xml.Xsl` | XSLT 변환 |

---

## Gaming — 게이밍

| 패키지 | 설명 |
|---|---|
| `Windows.Gaming.Input` | 게임패드, 아케이드 스틱, 레이싱 휠 입력 |
| `Windows.Gaming.Input.ForceFeedback` | 포스 피드백 (진동, 저항) |
| `Windows.Gaming.UI` | 게임 바 UI |
| `Windows.Gaming.XboxLive.Storage` | Xbox Live 클라우드 세이브 |

---

## ApplicationModel — 앱 모델

| 패키지 | 설명 |
|---|---|
| `Windows.ApplicationModel` | 패키지 정보, 앱 수명주기 |
| `Windows.ApplicationModel.Activation` | 앱 활성화 인자 |
| `Windows.ApplicationModel.AppService` | 앱 간 서비스 통신 |
| `Windows.ApplicationModel.Background` | 백그라운드 작업 트리거 |
| `Windows.ApplicationModel.Calls` | 전화 통화 |
| `Windows.ApplicationModel.Chat` | SMS/MMS 메시지 |
| `Windows.ApplicationModel.Contacts` | 연락처 접근 |
| `Windows.ApplicationModel.Core` | CoreApplication, 뷰 관리 |
| `Windows.ApplicationModel.DataTransfer` | 클립보드, 공유 계약 |
| `Windows.ApplicationModel.DataTransfer.DragDrop` | 드래그 앤 드롭 |
| `Windows.ApplicationModel.Email` | 이메일 |
| `Windows.ApplicationModel.ExtendedExecution` | 확장 실행 (앱 일시정지 방지) |
| `Windows.ApplicationModel.Resources` | 리소스 로더 (다국어) |
| `Windows.ApplicationModel.Search` | 검색 통합 |
| `Windows.ApplicationModel.Store` | 스토어 인앱 구매 |
| `Windows.ApplicationModel.UserActivities` | 타임라인 활동 카드 |
| `Windows.ApplicationModel.UserDataTasks` | 작업/할일 |
| `Windows.ApplicationModel.VoiceCommands` | Cortana 음성 명령 |

---

## Web — 웹

| 패키지 | 설명 |
|---|---|
| `Windows.Web` | 웹 에러 상태 |
| `Windows.Web.AtomPub` | Atom Publishing Protocol |
| `Windows.Web.Http` | HTTP 클라이언트 (HttpClient) |
| `Windows.Web.Http.Filters` | HTTP 필터 체인 |
| `Windows.Web.Http.Headers` | HTTP 헤더 파서 |
| `Windows.Web.Syndication` | RSS/Atom 피드 파서 |

---

## Globalization — 국제화

| 패키지 | 설명 |
|---|---|
| `Windows.Globalization` | 언어, 지역, 캘린더 |
| `Windows.Globalization.Collation` | 문자 정렬 |
| `Windows.Globalization.DateTimeFormatting` | 날짜/시간 포매팅 |
| `Windows.Globalization.Fonts` | 언어별 추천 폰트 |
| `Windows.Globalization.NumberFormatting` | 숫자/통화/퍼센트 포매팅 |
| `Windows.Globalization.PhoneNumberFormatting` | 전화번호 포매팅 |

---

## Management — 관리

| 패키지 | 설명 |
|---|---|
| `Windows.Management.Deployment` | 앱 패키지 배포/설치 |
| `Windows.Management.Policies` | MDM 정책 |
| `Windows.Management.Setup` | 기기 초기 설정 |
| `Windows.Management.Update` | 업데이트 관리자 |
| `Windows.Management.Workplace` | 작업 공간 설정 |

---

## Perception — 공간 인식 (Mixed Reality)

| 패키지 | 설명 |
|---|---|
| `Windows.Perception` | 타임스탬프 |
| `Windows.Perception.People` | 시선/손 추적 |
| `Windows.Perception.Spatial` | 공간 좌표계, 앵커 |
| `Windows.Perception.Spatial.Surfaces` | 공간 매핑 (3D 메시) |

---

## Services — 서비스

| 패키지 | 설명 |
|---|---|
| `Windows.Services.Maps` | Bing 지도, 경로 탐색 |
| `Windows.Services.Maps.Guidance` | 내비게이션 안내 |
| `Windows.Services.Maps.OfflineMaps` | 오프라인 지도 관리 |
| `Windows.Services.Store` | Microsoft Store 인앱 구매 (v2) |
