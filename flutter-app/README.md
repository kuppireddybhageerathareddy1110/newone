# CardioAI Flutter

This folder contains a Flutter client for the CardioAI FastAPI backend in the repository root.

## Current status

The Dart app source is present and organized, but this environment did not have the Flutter CLI installed, so generated platform folders such as `android/`, `ios/`, `web/`, `linux/`, `macos/`, and `windows/` were not created here.

That means:

- the app source is ready to continue
- you still need to run Flutter locally to generate platform folders and fetch packages

## Features currently included

- single-patient assessment
- batch CSV scoring
- insights from the latest prediction
- recent in-memory session history
- model details and feature glossary

## Prerequisites

- Flutter SDK installed
- a running backend from the repo root

Check Flutter:

```powershell
flutter --version
flutter doctor
```

## Backend dependency

This app depends on the backend in the repo root.

Start the backend first:

```powershell
cd ..
.\.venv\Scripts\Activate.ps1
uvicorn api_hybrid:app --host 0.0.0.0 --port 8001 --reload
```

## First-time Flutter setup

From this folder:

```powershell
cd flutter-app
flutter create .
flutter pub get
```

Important:

- keep the existing `lib/` and `pubspec.yaml` from this repo
- if Flutter warns about overwriting files, preserve the application code already added here

## Run the Flutter app

```powershell
flutter run
```

If multiple devices are available:

```powershell
flutter devices
flutter run -d <device-id>
```

## Backend URL configuration

The API base URL is currently defined in:

- [cardio_api.dart](C:\Users\k bhageeratha reddy\Downloads\newoneheart\flutter-app\lib\services\cardio_api.dart)

Default:

- `http://10.0.2.2:8001`

That is the correct value for an Android emulator talking to a backend running on your development machine.

Change it depending on target:

- Android emulator: `http://10.0.2.2:8001`
- Windows desktop Flutter app: `http://127.0.0.1:8001`
- physical device: `http://<your-local-ip>:8001`

## Folder overview

- `lib/main.dart`: app entry point
- `lib/app.dart`: app theme and root widget
- `lib/models/`: request and response models
- `lib/services/cardio_api.dart`: backend API integration
- `lib/screens/`: assessment, batch, insights, history, and model details screens

## Development flow

1. Start backend from repo root.
2. Open `flutter-app`.
3. Run `flutter pub get` if needed.
4. Run `flutter run`.
5. Adjust the base URL if your target device cannot reach the backend.

## Troubleshooting

### Flutter command not found

Flutter is not installed or not added to PATH.

### App starts but cannot reach backend

Check:

1. backend is running on port `8001`
2. `cardio_api.dart` uses the right host for your target device
3. firewall is not blocking the connection

### Physical phone cannot connect

Do not use `127.0.0.1`. Use your machine’s local network IP.

### `flutter create .` overwrites files

Keep the custom `lib/` code and `pubspec.yaml` that already exist in this folder.
