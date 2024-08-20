package main

import (
	"bytes"
	"encoding/json"
	"image"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/corona10/goimagehash"
	"github.com/disintegration/imaging"
	"github.com/otiai10/gosseract/v2"
	"github.com/patrickmn/go-cache"
)

var imageCache = cache.New(30*time.Second, 10*time.Minute)

func main() {
	// Setup logging to file
	logFilePath := "/logs/ocr.log" // Path inside the container
	logFile, err := os.OpenFile(logFilePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}
	defer logFile.Close()
	log.SetOutput(logFile)

	log.Println("Starting OCR server on :8080")
	http.HandleFunc("/", handleOCR)
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

// OCRResult holds the result of the OCR processing.
type OCRResult struct {
	DHash string `json:"dHash"`
	Text  string `json:"text"`
	Error string `json:"error,omitempty"`
}

// handleOCR processes incoming HTTP requests and performs OCR on provided images.
func handleOCR(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		log.Printf("Invalid method: %s", r.Method)
		return
	}

	err := r.ParseMultipartForm(10 << 20) // 10 MB max memory
	if err != nil {
		http.Error(w, "Unable to parse form, data too large.", http.StatusBadRequest)
		log.Printf("Failed to parse form: %v", err)
		return
	}

	files := r.MultipartForm.File["images"]
	log.Printf("Number of files received: %d", len(files))
	results := make([]OCRResult, len(files))
	var wg sync.WaitGroup

	for i, fileHeader := range files {
		wg.Add(1)
		go func(i int, fileHeader *multipart.FileHeader) {
			defer wg.Done()
			file, err := fileHeader.Open()
			if err != nil {
				log.Printf("Error opening file %s: %v", fileHeader.Filename, err)
				results[i] = OCRResult{Error: "Error opening file"}
				return
			}
			defer file.Close()

			dHash, text, err := processImage(file)
			if err != nil {
				log.Printf("Error processing file %s: %v", fileHeader.Filename, err)
				results[i] = OCRResult{DHash: dHash, Error: "Error processing image"}
			} else {
				log.Printf("Successfully processed file %s", fileHeader.Filename)
				results[i] = OCRResult{DHash: dHash, Text: text}
			}
		}(i, fileHeader)
	}

	wg.Wait()

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(results); err != nil {
		log.Printf("Failed to send response: %v", err)
	}
}

// processImage processes an image file, generating its hash and performing OCR.
func processImage(file io.Reader) (string, string, error) {
	startTime := time.Now()

	img, err := imaging.Decode(file)
	if err != nil {
		log.Printf("Error decoding image: %v", err)
		return "", "", err
	}
	// Scale image to 3x size
	img = imaging.Resize(img, 0, 2*img.Bounds().Dy(), imaging.Lanczos)

	// Convert image to grayscale
	grayImg := imaging.Grayscale(img)

	// Timing hash generation
	hashStart := time.Now()
	dHash, err := generateImageHash(grayImg)
	if err != nil {
		log.Printf("Error generating image hash: %v", err)
		return "", "", err
	}
	hashDuration := time.Since(hashStart)
	log.Printf("Time taken to generate hash: %v", hashDuration)

	if cachedResult, found := imageCache.Get(dHash); found {
		log.Printf("Image hash found in cache")
		return dHash, cachedResult.(string), nil
	}

	// Timing OCR processing
	ocrStart := time.Now()
	text, err := performOCR(grayImg)
	if err != nil {
		log.Printf("Error performing OCR: %v", err)
		return dHash, "", err
	}
	ocrDuration := time.Since(ocrStart)
	log.Printf("Time taken for OCR processing: %v", ocrDuration)

	imageCache.Set(dHash, text, cache.DefaultExpiration)
	totalDuration := time.Since(startTime)
	log.Printf("Total processing time: %v", totalDuration)

	return dHash, text, nil
}

// generateImageHash generates a hash for the given image.
func generateImageHash(img image.Image) (string, error) {
	startTime := time.Now()
	dHash, err := goimagehash.ExtDifferenceHash(img, 32, 32)
	if err != nil {
		log.Printf("Error generating image hash: %v", err)
		return "", err
	}
	duration := time.Since(startTime)
	log.Printf("Time taken to generate image hash: %v", duration)
	return dHash.ToString(), nil
}

// performOCR performs OCR on the given image and returns the extracted text.
func performOCR(img image.Image) (string, error) {
	client := gosseract.NewClient()
	defer client.Close()

	// Tesseract configuration for better results
	client.SetLanguage("eng")
	client.SetVariable("user_defined_dpi", "300")
	client.SetWhitelist("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-@_' ")
	client.SetPageSegMode(gosseract.PSM_SINGLE_LINE)

	buf := new(bytes.Buffer)
	err := imaging.Encode(buf, img, imaging.PNG)
	if err != nil {
		log.Printf("Error encoding image to PNG: %v", err)
		return "", err
	}

	client.SetImageFromBytes(buf.Bytes())

	// Timing OCR extraction
	startTime := time.Now()
	text, err := client.Text()
	if err != nil {
		log.Printf("Error extracting text from image: %v", err)
		return "", err
	}
	duration := time.Since(startTime)
	log.Printf("Time taken for OCR extraction: %v", duration)

	return text, nil
}
