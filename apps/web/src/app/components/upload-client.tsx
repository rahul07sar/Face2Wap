/**
 * ============================================================================
 * Face2Wap
 * ----------------------------------------------------------------------------
 * File:        upload-client.tsx
 * Module:      Web / Upload
 * Description:
 *
 * Provides the client-side Face2Wap upload workflow, including theme
 * persistence, upload mode selection, source and target file selection,
 * previews, upload progress, validation, retries, backend integration, image
 * processing dispatch, and live job-status polling.
 *
 * ============================================================================
 */

"use client";

import {
  ChangeEvent,
  DragEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import styles from "../page.module.css";


type ThemeMode = "light" | "dark";

type UploadMode = "photo" | "video" | "gif";

type UploadState =
  | "idle"
  | "creating"
  | "preparing"
  | "uploading"
  | "completing"
  | "completed"
  | "failed";

type ProcessingState =
  | "idle"
  | "queueing"
  | "queued"
  | "processing"
  | "completed"
  | "failed";

type UploadStep = 1 | 2;

type CreateJobResponse = {
  jobId: string;
  jobToken: string;
  status: string;
  expiresAt: string;
};

type PrepareUploadResponse = {
  assetId: number;
  uploadUrl: string;
  objectPath: string;
  storageProvider: string;
  uploadExpiresAt: string;
};

type CompleteUploadResponse = {
  assetId: number;
  jobId: string;
  assetType: string;
  uploadStatus: string;
  jobReadyForQueue: boolean;
};

type QueueImageSwapResponse = {
  jobId: string;
  jobType: string;
  status: string;
  progressPercent: number;
};

type JobStatusResponse = {
  jobId: string;
  jobType: string;
  status: string;
  progressPercent: number;
  errorMessage: string | null;
  expiresAt: string;
};

type JobResultFileResponse = {
  jobId: string;
  status: string;
  resultUrl: string | null;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;

const THEME_STORAGE_KEY =
  "face2wap-theme";

const STATUS_POLL_INTERVAL_MS =
  4_000;

const SOURCE_IMAGE_ACCEPT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];

const TARGET_IMAGE_ACCEPT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];

const TARGET_VIDEO_ACCEPT_TYPES = [
  "video/mp4",
  "video/webm",
  "video/quicktime",
];

const MAX_SOURCE_IMAGE_SIZE_BYTES =
  50 * 1024 * 1024;

const MAX_TARGET_IMAGE_SIZE_BYTES =
  50 * 1024 * 1024;

const MAX_TARGET_VIDEO_SIZE_BYTES =
  2 * 1024 * 1024 * 1024;


function requireApiBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error(
      "NEXT_PUBLIC_API_BASE_URL is not configured.",
    );
  }

  return API_BASE_URL.replace(/\/+$/, "");
}


function formatFileSize(sizeBytes: number): string {
  if (sizeBytes >= 1024 * 1024 * 1024) {
    return `${(
      sizeBytes /
      1024 /
      1024 /
      1024
    ).toFixed(2)} GB`;
  }

  return `${(
    sizeBytes /
    1024 /
    1024
  ).toFixed(2)} MB`;
}


function normalizeProgress(
  progressPercent: number,
): number {
  if (!Number.isFinite(progressPercent)) {
    return 0;
  }

  return Math.min(
    100,
    Math.max(
      0,
      Math.round(progressPercent),
    ),
  );
}


async function readErrorMessage(
  response: Response,
  fallbackMessage: string,
): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string;
    };

    return payload.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}


export default function UploadClient() {
  const [theme, setTheme] =
    useState<ThemeMode>("dark");

  const [uploadMode, setUploadMode] =
    useState<UploadMode>("photo");

  const [currentStep, setCurrentStep] =
    useState<UploadStep>(1);

  const [sourceFile, setSourceFile] =
    useState<File | null>(null);

  const [targetFile, setTargetFile] =
    useState<File | null>(null);

  const [sourcePreviewUrl, setSourcePreviewUrl] =
    useState<string | null>(null);

  const [targetPreviewUrl, setTargetPreviewUrl] =
    useState<string | null>(null);

  const [sourceDragging, setSourceDragging] =
    useState(false);

  const [targetDragging, setTargetDragging] =
    useState(false);

  const [sourceUploadState, setSourceUploadState] =
    useState<UploadState>("idle");

  const [targetUploadState, setTargetUploadState] =
    useState<UploadState>("idle");

  const [sourceUploadProgress, setSourceUploadProgress] =
    useState(0);

  const [targetUploadProgress, setTargetUploadProgress] =
    useState(0);

  const [sourceError, setSourceError] =
    useState<string | null>(null);

  const [targetError, setTargetError] =
    useState<string | null>(null);

  const [jobId, setJobId] =
    useState<string | null>(null);

  const [jobToken, setJobToken] =
    useState<string | null>(null);

  const [jobReadyForQueue, setJobReadyForQueue] =
    useState(false);

  const [processingState, setProcessingState] =
    useState<ProcessingState>("idle");

  const [processingProgress, setProcessingProgress] =
    useState(0);

  const [processingError, setProcessingError] =
    useState<string | null>(null);

  const [resultImageUrl, setResultImageUrl] =
  useState<string | null>(null);

  const [downloadingResult, setDownloadingResult] =
    useState(false);  

  const sourceInputRef =
    useRef<HTMLInputElement | null>(null);

  const targetInputRef =
    useRef<HTMLInputElement | null>(null);

  const statusPollTimeoutRef =
    useRef<number | null>(null);


  useEffect(() => {
    const savedTheme =
      window.localStorage.getItem(
        THEME_STORAGE_KEY,
      );

    if (
      savedTheme === "light" ||
      savedTheme === "dark"
    ) {
      setTheme(savedTheme);

      document.documentElement.dataset.theme =
        savedTheme;

      return;
    }

    document.documentElement.dataset.theme =
      "dark";
  }, []);


  useEffect(() => {
    if (!sourceFile) {
      setSourcePreviewUrl(null);

      return;
    }

    const nextPreviewUrl =
      URL.createObjectURL(sourceFile);

    setSourcePreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [sourceFile]);


  useEffect(() => {
    if (!targetFile) {
      setTargetPreviewUrl(null);

      return;
    }

    const nextPreviewUrl =
      URL.createObjectURL(targetFile);

    setTargetPreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [targetFile]);


  useEffect(() => {
    return () => {
      if (
        statusPollTimeoutRef.current !==
        null
      ) {
        window.clearTimeout(
          statusPollTimeoutRef.current,
        );
      }
    };
  }, []);


  function stopStatusPolling() {
    if (
      statusPollTimeoutRef.current === null
    ) {
      return;
    }

    window.clearTimeout(
      statusPollTimeoutRef.current,
    );

    statusPollTimeoutRef.current = null;
  }


  function resetProcessingState() {
    stopStatusPolling();

    setProcessingState("idle");
    setProcessingProgress(0);
    setProcessingError(null);
  }


  function toggleTheme() {
    const nextTheme: ThemeMode =
      theme === "dark"
        ? "light"
        : "dark";

    setTheme(nextTheme);

    window.localStorage.setItem(
      THEME_STORAGE_KEY,
      nextTheme,
    );

    document.documentElement.dataset.theme =
      nextTheme;
  }


  function selectUploadMode(
    nextMode: UploadMode,
  ) {
    if (
      sourceUploadState !== "idle" ||
      targetUploadState !== "idle"
    ) {
      return;
    }

    if (nextMode === "gif") {
      setSourceError(
        "GIF face swap support will be enabled after the image and video workflows.",
      );

      return;
    }

    setUploadMode(nextMode);
    setSourceError(null);
  }


  function openSourceFilePicker() {
    sourceInputRef.current?.click();
  }


  function openTargetFilePicker() {
    targetInputRef.current?.click();
  }


  function validateSourceFile(
    file: File,
  ): string | null {
    if (
      !SOURCE_IMAGE_ACCEPT_TYPES.includes(
        file.type,
      )
    ) {
      return "Select a JPG, PNG, or WebP source image.";
    }

    if (
      file.size >
      MAX_SOURCE_IMAGE_SIZE_BYTES
    ) {
      return "Source image must not exceed 50 MB.";
    }

    return null;
  }


  function validateTargetFile(
    file: File,
  ): string | null {
    if (uploadMode === "photo") {
      if (
        !TARGET_IMAGE_ACCEPT_TYPES.includes(
          file.type,
        )
      ) {
        return "Select a JPG, PNG, or WebP target image.";
      }

      if (
        file.size >
        MAX_TARGET_IMAGE_SIZE_BYTES
      ) {
        return "Target image must not exceed 50 MB.";
      }

      return null;
    }

    if (
      !TARGET_VIDEO_ACCEPT_TYPES.includes(
        file.type,
      )
    ) {
      return "Select an MP4, WebM, or MOV target video.";
    }

    if (
      file.size >
      MAX_TARGET_VIDEO_SIZE_BYTES
    ) {
      return "Target video must not exceed 2 GB.";
    }

    return null;
  }


  function handleSourceFile(
    file: File | undefined,
  ) {
    if (!file) {
      return;
    }

    const validationError =
      validateSourceFile(file);

    if (validationError) {
      setSourceFile(null);
      setSourceError(validationError);

      return;
    }

    setSourceFile(file);
    setSourceError(null);
    setSourceUploadState("idle");
    setSourceUploadProgress(0);

    resetProcessingState();
  }


  function handleTargetFile(
    file: File | undefined,
  ) {
    if (!file) {
      return;
    }

    const validationError =
      validateTargetFile(file);

    if (validationError) {
      setTargetFile(null);
      setTargetError(validationError);

      return;
    }

    setTargetFile(file);
    setTargetError(null);
    setTargetUploadState("idle");
    setTargetUploadProgress(0);
    setJobReadyForQueue(false);

    resetProcessingState();
  }


  function handleSourceInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    handleSourceFile(
      event.target.files?.[0],
    );

    event.target.value = "";
  }


  function handleTargetInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    handleTargetFile(
      event.target.files?.[0],
    );

    event.target.value = "";
  }


  function handleSourceDragOver(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    event.dataTransfer.dropEffect =
      "copy";

    setSourceDragging(true);
  }


  function handleTargetDragOver(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    event.dataTransfer.dropEffect =
      "copy";

    setTargetDragging(true);
  }


  function handleSourceDrop(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setSourceDragging(false);

    handleSourceFile(
      event.dataTransfer.files?.[0],
    );
  }


  function handleTargetDrop(
    event: DragEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    setTargetDragging(false);

    handleTargetFile(
      event.dataTransfer.files?.[0],
    );
  }


  function handleDropZoneKeyDown(
    event: KeyboardEvent<HTMLDivElement>,
    openPicker: () => void,
  ) {
    if (
      event.key === "Enter" ||
      event.key === " "
    ) {
      event.preventDefault();

      openPicker();
    }
  }


  function resetEntireWorkflow() {
    stopStatusPolling();

    setCurrentStep(1);

    setSourceFile(null);
    setTargetFile(null);

    setSourceError(null);
    setTargetError(null);

    setSourceUploadState("idle");
    setTargetUploadState("idle");

    setSourceUploadProgress(0);
    setTargetUploadProgress(0);

    setJobId(null);
    setJobToken(null);
    setJobReadyForQueue(false);

    setProcessingState("idle");
    setProcessingProgress(0);
    setProcessingError(null);

    setResultImageUrl(null);
    setDownloadingResult(false);
  }


  function removeTargetFile() {
    setTargetFile(null);
    setTargetError(null);
    setTargetUploadState("idle");
    setTargetUploadProgress(0);
    setJobReadyForQueue(false);
    resetProcessingState();
    setResultImageUrl(null);
  }


  function uploadFileWithProgress(
    uploadUrl: string,
    file: File,
    setProgress: (
      progress: number,
    ) => void,
  ): Promise<void> {
    return new Promise(
      (resolve, reject) => {
        const formData =
          new FormData();

        formData.append(
          "file",
          file,
          file.name,
        );

        const request =
          new XMLHttpRequest();

        request.upload.onprogress = (
          event,
        ) => {
          if (!event.lengthComputable) {
            return;
          }

          setProgress(
            Math.round(
              (event.loaded /
                event.total) *
                100,
            ),
          );
        };

        request.onload = () => {
          if (
            request.status >= 200 &&
            request.status < 300
          ) {
            resolve();

            return;
          }

          let message =
            "File upload failed.";

          try {
            const payload =
              JSON.parse(
                request.responseText,
              ) as {
                detail?: string;
              };

            message =
              payload.detail || message;
          } catch {
            // Preserve the fallback message.
          }

          reject(new Error(message));
        };

        request.onerror = () => {
          reject(
            new Error(
              "Network error while uploading file.",
            ),
          );
        };

        request.open(
          "POST",
          uploadUrl,
        );

        request.setRequestHeader(
          "Accept",
          "application/json",
        );

        request.send(formData);
      },
    );
  }


  async function prepareAndUploadAsset(
    activeJobId: string,
    file: File,
    assetType:
      | "SOURCE_FACE_IMAGE"
      | "TARGET_IMAGE"
      | "TARGET_VIDEO",
    setState: (
      state: UploadState,
    ) => void,
    setProgress: (
      progress: number,
    ) => void,
  ): Promise<CompleteUploadResponse> {
    const apiBaseUrl =
      requireApiBaseUrl();

    setState("preparing");

    const prepareResponse =
      await fetch(
        `${apiBaseUrl}/jobs/${activeJobId}/uploads/prepare`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            assetType,
            filename: file.name,
            mimeType: file.type,
            sizeBytes: file.size,
          }),
        },
      );

    if (!prepareResponse.ok) {
      throw new Error(
        await readErrorMessage(
          prepareResponse,
          "Could not prepare the upload.",
        ),
      );
    }

    const prepared =
      (await prepareResponse.json()) as PrepareUploadResponse;

    setState("uploading");

    await uploadFileWithProgress(
      `${apiBaseUrl}${prepared.uploadUrl}`,
      file,
      setProgress,
    );

    setState("completing");

    const completeResponse =
      await fetch(
        `${apiBaseUrl}/jobs/${activeJobId}/assets/${prepared.assetId}/complete`,
        {
          method: "POST",
        },
      );

    if (!completeResponse.ok) {
      throw new Error(
        await readErrorMessage(
          completeResponse,
          "Could not complete the upload.",
        ),
      );
    }

    return (
      (await completeResponse.json()) as CompleteUploadResponse
    );
  }


  async function uploadSourceFace() {
    if (
      !sourceFile ||
      sourceUploadState === "uploading"
    ) {
      return;
    }

    try {
      const apiBaseUrl =
        requireApiBaseUrl();

      setSourceError(null);
      setSourceUploadProgress(0);
      setSourceUploadState("creating");

      const jobResponse =
        await fetch(
          `${apiBaseUrl}/jobs`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              jobType:
                uploadMode === "video"
                  ? "VIDEO_SWAP"
                  : "IMAGE_SWAP",
            }),
          },
        );

      if (!jobResponse.ok) {
        throw new Error(
          await readErrorMessage(
            jobResponse,
            "Could not create the job.",
          ),
        );
      }

      const job =
        (await jobResponse.json()) as CreateJobResponse;

      setJobId(job.jobId);
      setJobToken(job.jobToken);

      await prepareAndUploadAsset(
        job.jobId,
        sourceFile,
        "SOURCE_FACE_IMAGE",
        setSourceUploadState,
        setSourceUploadProgress,
      );

      setSourceUploadProgress(100);
      setSourceUploadState("completed");
      setCurrentStep(2);
    } catch (error) {
      setSourceUploadState("failed");

      setSourceError(
        error instanceof Error
          ? error.message
          : "Source upload failed.",
      );
    }
  }


  async function uploadTargetFile() {
    if (
      !targetFile ||
      !jobId ||
      !jobToken ||
      targetUploadState === "uploading"
    ) {
      return;
    }

    try {
      setTargetError(null);
      setTargetUploadProgress(0);

      const assetType =
        uploadMode === "video"
          ? "TARGET_VIDEO"
          : "TARGET_IMAGE";

      const result =
        await prepareAndUploadAsset(
          jobId,
          targetFile,
          assetType,
          setTargetUploadState,
          setTargetUploadProgress,
        );

      setTargetUploadProgress(100);
      setTargetUploadState("completed");
      setJobReadyForQueue(
        result.jobReadyForQueue,
      );
    } catch (error) {
      setTargetUploadState("failed");

      setTargetError(
        error instanceof Error
          ? error.message
          : "Target upload failed.",
      );
    }
  }

async function loadCompletedResult(
  activeJobId: string,
): Promise<void> {
  if (!jobToken) {
    throw new Error(
      "The result is unavailable at the moment, please try again later or contact support if the issue persists.",
    );
  }

  const apiBaseUrl =
    requireApiBaseUrl();

  const response = await fetch(
    `${apiBaseUrl}/jobs/${activeJobId}/result?token=${encodeURIComponent(
      jobToken,
    )}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(
        response,
        "Could not load the generated result.",
      ),
    );
  }

  const result =
    (await response.json()) as JobResultFileResponse;

  if (!result.resultUrl) {
    throw new Error(
      "The generated result is unavailable.",
    );
  }

  const absoluteResultUrl =
    result.resultUrl.startsWith("http://") ||
    result.resultUrl.startsWith("https://")
      ? result.resultUrl
      : `${apiBaseUrl}${result.resultUrl}`;

  setResultImageUrl(
    absoluteResultUrl,
  );
}

async function downloadCompletedResult() {
  if (
    !resultImageUrl ||
    downloadingResult
  ) {
    return;
  }

  try {
    setDownloadingResult(true);
    setProcessingError(null);

    const separator =
      resultImageUrl.includes("?")
        ? "&"
        : "?";

    const response = await fetch(
      `${resultImageUrl}${separator}download=true`,
      {
        method: "GET",
        headers: {
          Accept: "image/*",
        },
        cache: "no-store",
      },
    );

    if (!response.ok) {
      throw new Error(
        await readErrorMessage(
          response,
          "Could not download the generated result.",
        ),
      );
    }

    const resultBlob =
      await response.blob();

    const downloadUrl =
      URL.createObjectURL(resultBlob);

    const downloadLink =
      document.createElement("a");

    downloadLink.href =
      downloadUrl;

    downloadLink.download =
      "face2wap-result.png";

    document.body.appendChild(
      downloadLink,
    );

    downloadLink.click();
    downloadLink.remove();

    URL.revokeObjectURL(
      downloadUrl,
    );
  } catch (error) {
    setProcessingError(
      error instanceof Error
        ? error.message
        : "Could not download the generated result.",
    );
  } finally {
    setDownloadingResult(false);
  }
}

  async function pollJobStatus(
    activeJobId: string,
  ): Promise<void> {
    try {
      const apiBaseUrl =
        requireApiBaseUrl();

      const response = await fetch(
        `${apiBaseUrl}/jobs/${activeJobId}/status`,
        {
          method: "GET",
          headers: {
            Accept: "application/json",
          },
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(
          await readErrorMessage(
            response,
            "Could not read processing status.",
          ),
        );
      }

      const result =
        (await response.json()) as JobStatusResponse;

      const nextProgress =
        normalizeProgress(
          result.progressPercent,
        );

      setProcessingProgress(nextProgress);

      if (result.status === "COMPLETED") {
        stopStatusPolling();

        setProcessingState("completed");
        setProcessingProgress(100);
        setProcessingError(null);

          await loadCompletedResult(
           activeJobId,
        );

        return;
      }

      if (
        result.status === "FAILED" ||
        result.status === "EXPIRED" ||
        result.status === "BLOCKED"
      ) {
        stopStatusPolling();

        setProcessingState("failed");

        setProcessingError(
          result.errorMessage ||
            `Processing stopped with status ${result.status}.`,
        );

        return;
      }

      if (result.status === "PROCESSING") {
        setProcessingState("processing");
      } else {
        setProcessingState("queued");
      }

      statusPollTimeoutRef.current =
        window.setTimeout(
          () => {
            void pollJobStatus(activeJobId);
          },
          STATUS_POLL_INTERVAL_MS,
        );
    } catch (error) {
      stopStatusPolling();

      setProcessingState("failed");

      setProcessingError(
        error instanceof Error
          ? error.message
          : "Could not track processing progress.",
      );
    }
  }


  async function startImageProcessing() {
    if (
      uploadMode !== "photo" ||
      !jobId ||
      !jobToken ||
      !jobReadyForQueue ||
      processingState === "queueing" ||
      processingState === "queued" ||
      processingState === "processing" ||
      processingState === "completed"
    ) {
      return;
    }

    try {
      const apiBaseUrl =
        requireApiBaseUrl();

      stopStatusPolling();

      setProcessingState("queueing");
      setProcessingProgress(0);
      setProcessingError(null);
      setResultImageUrl(null);

      const response = await fetch(
        `${apiBaseUrl}/jobs/${jobId}/process-image?token=${encodeURIComponent(
          jobToken,
        )}`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
        },
      );

      if (!response.ok) {
        throw new Error(
          await readErrorMessage(
            response,
            "Could not start the face swap.",
          ),
        );
      }

      const result =
        (await response.json()) as QueueImageSwapResponse;

      setProcessingState("queued");

      setProcessingProgress(
        normalizeProgress(
          result.progressPercent,
        ),
      );

      void pollJobStatus(jobId);
    } catch (error) {
      stopStatusPolling();

      setProcessingState("failed");

      setProcessingError(
        error instanceof Error
          ? error.message
          : "Could not start the face swap.",
      );
    }
  }


  const sourceUploadBusy = [
    "creating",
    "preparing",
    "uploading",
    "completing",
  ].includes(sourceUploadState);

  const targetUploadBusy = [
    "preparing",
    "uploading",
    "completing",
  ].includes(targetUploadState);

  const processingBusy = [
    "queueing",
    "queued",
    "processing",
  ].includes(processingState);

  const targetAccept =
    uploadMode === "video"
      ? TARGET_VIDEO_ACCEPT_TYPES.join(",")
      : TARGET_IMAGE_ACCEPT_TYPES.join(",");

  const targetTitle =
    uploadMode === "video"
      ? "Upload target video"
      : "Upload target image";

  const targetDropText =
    uploadMode === "video"
      ? "Drop your target video here"
      : "Drop your target image here";

  const targetChooseText =
    uploadMode === "video"
      ? "Choose video"
      : "Choose image";

  const processingStatusTitle =
    processingState === "queueing"
      ? "Starting face swap"
      : processingState === "queued"
        ? "Face swap queued"
        : processingState === "processing"
          ? "Processing face swap"
          : processingState === "completed"
            ? "Face swap completed"
            : processingState === "failed"
              ? "Face swap failed"
              : "";

  const processingStatusMessage =
    processingState === "queueing"
      ? "Submitting your image face-swap job."
      : processingState === "queued"
        ? "Your job is waiting for the worker."
        : processingState === "processing"
          ? `Your images are being processed. ${processingProgress}% complete.`
          : processingState === "completed"
            ? "Your face-swap result has been generated successfully."
            : processingState === "failed"
              ? "The face-swap job could not be completed."
              : "";


  return (
    <section
      id="upload"
      className={styles.uploadPanel}
      aria-labelledby="upload-title"
    >
      <div className={styles.uploadHeader}>
        <div>
          <span className={styles.step}>
            Step {currentStep} of 2
          </span>

          <h2 id="upload-title">
            {currentStep === 1
              ? "Upload source face"
              : targetTitle}
          </h2>
        </div>

        <button
          className={styles.themeToggle}
          type="button"
          onClick={toggleTheme}
          aria-label={`Switch to ${
            theme === "dark"
              ? "light"
              : "dark"
          } mode`}
        >
          {theme === "dark"
            ? "Light Mode"
            : "Dark Mode"}
        </button>
      </div>

      <div
        className={styles.uploadTabs}
        role="tablist"
        aria-label="Face swap type"
      >
        <button
          className={
            uploadMode === "photo"
              ? styles.activeTab
              : undefined
          }
          type="button"
          role="tab"
          aria-selected={
            uploadMode === "photo"
          }
          disabled={
            sourceUploadState !== "idle"
          }
          onClick={() =>
            selectUploadMode("photo")
          }
        >
          Photo Face Swap
        </button>

        <button
          className={
            uploadMode === "video"
              ? styles.activeTab
              : undefined
          }
          type="button"
          role="tab"
          aria-selected={
            uploadMode === "video"
          }
          disabled={
            sourceUploadState !== "idle"
          }
          onClick={() =>
            selectUploadMode("video")
          }
        >
          Video Face Swap
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={false}
          aria-disabled="true"
          disabled
          title="GIF support is planned"
        >
          GIF Face Swap
        </button>
      </div>

      {currentStep === 1 ? (
        <>
          <input
            ref={sourceInputRef}
            className={
              styles.hiddenFileInput
            }
            type="file"
            accept={
              SOURCE_IMAGE_ACCEPT_TYPES.join(
                ",",
              )
            }
            onChange={
              handleSourceInputChange
            }
          />

          <div
            className={`${styles.dropZone} ${
              sourceDragging
                ? styles.dropZoneActive
                : ""
            }`}
            role="button"
            tabIndex={0}
            aria-label="Select source face image"
            onClick={
              openSourceFilePicker
            }
            onKeyDown={(event) =>
              handleDropZoneKeyDown(
                event,
                openSourceFilePicker,
              )
            }
            onDragOver={
              handleSourceDragOver
            }
            onDragLeave={() =>
              setSourceDragging(false)
            }
            onDrop={handleSourceDrop}
          >
            {sourcePreviewUrl &&
            sourceFile ? (
              <div
                className={
                  styles.previewBox
                }
              >
                <img
                  className={
                    styles.previewImage
                  }
                  src={sourcePreviewUrl}
                  alt="Selected source face preview"
                />

                <div
                  className={
                    styles.previewMeta
                  }
                >
                  <strong>
                    {sourceFile.name}
                  </strong>

                  <span>
                    {formatFileSize(
                      sourceFile.size,
                    )}
                  </span>
                </div>

                <button
                  className={
                    styles.removeFileButton
                  }
                  type="button"
                  disabled={
                    sourceUploadBusy
                  }
                  onClick={(event) => {
                    event.stopPropagation();

                    resetEntireWorkflow();
                  }}
                >
                  Remove
                </button>
              </div>
            ) : (
              <>
                <div
                  className={
                    styles.uploadIcon
                  }
                  aria-hidden="true"
                >
                  ↑
                </div>

                <h3>
                  Drop your face image here
                </h3>

                <p>
                  Drag and drop a source
                  image or choose one from
                  your device.
                </p>

                <button
                  className={
                    styles.fileButton
                  }
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();

                    openSourceFilePicker();
                  }}
                >
                  Choose image
                </button>
              </>
            )}
          </div>

          {sourceFile ? (
            <button
              className={
                styles.uploadActionButton
              }
              type="button"
              disabled={
                sourceUploadBusy ||
                sourceUploadState ===
                  "completed"
              }
              onClick={uploadSourceFace}
            >
              {sourceUploadState ===
                "creating" &&
                "Creating job..."}

              {sourceUploadState ===
                "preparing" &&
                "Preparing upload..."}

              {sourceUploadState ===
                "uploading" &&
                `Uploading ${sourceUploadProgress}%`}

              {sourceUploadState ===
                "completing" &&
                "Completing upload..."}

              {sourceUploadState ===
                "completed" &&
                "Source face uploaded"}

              {sourceUploadState ===
                "failed" &&
                "Retry source upload"}

              {sourceUploadState ===
                "idle" &&
                "Upload source face"}
            </button>
          ) : null}

          {sourceUploadState !==
          "idle" ? (
            <div
              className={
                styles.progressTrack
              }
              aria-label="Source upload progress"
            >
              <span
                style={{
                  width: `${sourceUploadProgress}%`,
                }}
              />
            </div>
          ) : null}

          {sourceError ? (
            <p
              className={styles.fileError}
              role="alert"
            >
              {sourceError}
            </p>
          ) : null}
        </>
      ) : (
        <>
          <input
            ref={targetInputRef}
            className={
              styles.hiddenFileInput
            }
            type="file"
            accept={targetAccept}
            onChange={
              handleTargetInputChange
            }
          />

          <div
            className={`${styles.dropZone} ${
              targetDragging
                ? styles.dropZoneActive
                : ""
            }`}
            role="button"
            tabIndex={0}
            aria-label={targetTitle}
            onClick={
              openTargetFilePicker
            }
            onKeyDown={(event) =>
              handleDropZoneKeyDown(
                event,
                openTargetFilePicker,
              )
            }
            onDragOver={
              handleTargetDragOver
            }
            onDragLeave={() =>
              setTargetDragging(false)
            }
            onDrop={handleTargetDrop}
          >
            {targetPreviewUrl &&
            targetFile ? (
              <div
                className={
                  styles.previewBox
                }
              >
                {uploadMode ===
                "video" ? (
                  <video
                    className={
                      styles.previewImage
                    }
                    src={targetPreviewUrl}
                    controls
                    preload="metadata"
                    onClick={(event) =>
                      event.stopPropagation()
                    }
                  />
                ) : (
                  <img
                    className={
                      styles.previewImage
                    }
                    src={targetPreviewUrl}
                    alt="Selected target preview"
                  />
                )}

                <div
                  className={
                    styles.previewMeta
                  }
                >
                  <strong>
                    {targetFile.name}
                  </strong>

                  <span>
                    {formatFileSize(
                      targetFile.size,
                    )}
                  </span>
                </div>

                <button
                  className={
                    styles.removeFileButton
                  }
                  type="button"
                  disabled={
                    targetUploadBusy ||
                    processingBusy
                  }
                  onClick={(event) => {
                    event.stopPropagation();

                    removeTargetFile();
                  }}
                >
                  Remove
                </button>
              </div>
            ) : (
              <>
                <div
                  className={
                    styles.uploadIcon
                  }
                  aria-hidden="true"
                >
                  ↑
                </div>

                <h3>
                  {targetDropText}
                </h3>

                <p>
                  Drag and drop the target
                  file or choose one from
                  your device.
                </p>

                <button
                  className={
                    styles.fileButton
                  }
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();

                    openTargetFilePicker();
                  }}
                >
                  {targetChooseText}
                </button>
              </>
            )}
          </div>

          {targetFile ? (
            <button
              className={
                styles.uploadActionButton
              }
              type="button"
              disabled={
                targetUploadBusy ||
                targetUploadState ===
                  "completed"
              }
              onClick={uploadTargetFile}
            >
              {targetUploadState ===
                "preparing" &&
                "Preparing target..."}

              {targetUploadState ===
                "uploading" &&
                `Uploading ${targetUploadProgress}%`}

              {targetUploadState ===
                "completing" &&
                "Completing target..."}

              {targetUploadState ===
                "completed" &&
                "Target uploaded"}

              {targetUploadState ===
                "failed" &&
                "Retry target upload"}

              {targetUploadState ===
                "idle" &&
                `Upload ${
                  uploadMode === "video"
                    ? "target video"
                    : "target image"
                }`}
            </button>
          ) : null}

          {targetUploadState !==
          "idle" ? (
            <div
              className={
                styles.progressTrack
              }
              aria-label="Target upload progress"
            >
              <span
                style={{
                  width: `${targetUploadProgress}%`,
                }}
              />
            </div>
          ) : null}

          {targetError ? (
            <p
              className={styles.fileError}
              role="alert"
            >
              {targetError}
            </p>
          ) : null}

          {jobReadyForQueue &&
          processingState === "idle" ? (
            <div
              className={
                styles.uploadSuccess
              }
              role="status"
            >
              <strong>
                Files uploaded successfully
              </strong>

              <span>
                Your face-swap job is ready
                for processing.
              </span>
            </div>
          ) : null}

          {jobReadyForQueue &&
          uploadMode === "photo" ? (
            <button
              className={
                styles.uploadActionButton
              }
              type="button"
              disabled={
                processingBusy ||
                processingState ===
                  "completed" ||
                processingState ===
                  "failed"
              }
              onClick={
                startImageProcessing
              }
            >
              {processingState ===
                "idle" &&
                "Start Face Swap"}

              {processingState ===
                "queueing" &&
                "Starting Face Swap..."}

              {processingState ===
                "queued" &&
                "Face Swap Queued"}

              {processingState ===
                "processing" &&
                `Processing ${processingProgress}%`}

              {processingState ===
                "completed" &&
                "Face Swap Completed"}

              {processingState ===
                "failed" &&
                "Face Swap Failed"}
            </button>
          ) : null}

          {processingState !== "idle" ? (
            <>
              <div
                className={
                  styles.uploadSuccess
                }
                role="status"
                aria-live="polite"
              >
                <strong>
                  {processingStatusTitle}
                </strong>

                <span>
                  {processingStatusMessage}
                </span>
              </div>

              <div
                className={
                  styles.progressTrack
                }
                role="progressbar"
                aria-label="Face-swap processing progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={
                  processingProgress
                }
              >
                <span
                  style={{
                    width: `${processingProgress}%`,
                  }}
                />
              </div>
            </>
          ) : null}

          {processingState === "completed" &&
            resultImageUrl ? (
              <div
                className={styles.previewBox}
                role="region"
                aria-label="Generated result"
              >
                <img
                  className={styles.previewImage}
                  src={resultImageUrl}
                  alt="Generated Face2Wap result"
                />

                <button
                  className={
                    styles.uploadActionButton
                  }
                  type="button"
                  disabled={
                    downloadingResult
                  }
                  onClick={
                    downloadCompletedResult
                  }
                >
                  {downloadingResult
                    ? "Preparing download..."
                    : "Download Result"}
                </button>

                <button
                  className={
                    styles.secondaryActionButton
                  }
                  type="button"
                  onClick={
                    resetEntireWorkflow
                  }
                >
                  Swap Another Image
                </button>
              </div>
            ) : null}

          {processingError ? (
            <p
              className={styles.fileError}
              role="alert"
            >
              {processingError}
            </p>
          ) : null}

          <button
            className={
              styles.secondaryActionButton
            }
            type="button"
            disabled={
              targetUploadBusy ||
              processingBusy
            }
            onClick={() =>
              setCurrentStep(1)
            }
          >
            Back to source image
          </button>
        </>
      )}

      <div className={styles.privacyNote}>
        <span aria-hidden="true">
          ◉
        </span>

        <p>
          Uploads are private and
          automatically removed after expiry.
        </p>
      </div>
    </section>
  );
}
