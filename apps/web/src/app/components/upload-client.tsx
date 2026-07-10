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
 * previews, upload progress, validation, retries, and backend integration.
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


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;

const THEME_STORAGE_KEY =
  "face2wap-theme";

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

  const sourceInputRef =
    useRef<HTMLInputElement | null>(null);

  const targetInputRef =
    useRef<HTMLInputElement | null>(null);


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
  }


  function removeTargetFile() {
    setTargetFile(null);
    setTargetError(null);
    setTargetUploadState("idle");
    setTargetUploadProgress(0);
    setJobReadyForQueue(false);
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
                    targetUploadBusy
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

          {jobReadyForQueue ? (
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

          <button
            className={
              styles.secondaryActionButton
            }
            type="button"
            disabled={targetUploadBusy}
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
