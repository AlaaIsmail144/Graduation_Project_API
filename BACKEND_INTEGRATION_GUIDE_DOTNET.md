# 🔌 Unified API - Backend Integration Guide (.NET)

**Simple Guide for .NET Backend Developers**

---

## 📌 What You Need to Know

This API combines **two systems** in one service on port **8000**:

1. **Recommendations** (`/api/v2/*`) - Match students with internships
2. **Topics** (`/api/v1/*`) - Auto-categorize internships

---

## 📁 Project Structure

```
unified-api/
├── app/
│   ├── __init__.py
│   ├── main.py                          # ✨ Main entry point (unified API)
│   │
│   ├── 📁 internship/                   # Topic Modeling System (V1)
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── topics.py                # /api/v1/topics/*
│   │   │   └── assignments.py           # /api/v1/assignments/*
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                # Internship system settings
│   │   │   ├── database.py              # Database connection
│   │   │   ├── events.py                # Startup/shutdown logic
│   │   │   └── startup_utils.py         # Initialization helpers
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── clustering.py            # Topic clustering logic
│   │   │   ├── assignment.py            # Topic assignment service
│   │   │   └── vector_db.py             # ChromaDB for topics
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py               # Request/response models
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── preprocessing.py         # Text cleaning utilities
│   │
│   └── 📁 recommendations/              # Recommendation Engine (V2)
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py                # Recommendation system settings
│       │   ├── database.py              # Database connection
│       │   ├── events.py                # Startup/shutdown logic
│       │   └── startup_utils.py         # Vector DB initialization
│       ├── services/
│       │   ├── __init__.py
│       │   ├── data_service.py          # In-memory cache management
│       │   ├── vector_service.py        # ChromaDB operations
│       │   ├── sync_service.py          # Incremental updates
│       │   ├── recommendation_service.py # Recommendation logic
│       │   ├── ranking_service.py       # Hybrid ranking (15 signals)
│       │   └── search_service.py        # Semantic search
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── recommendations.py   # /api/v2/recommendations/*
│       │   │   ├── search.py            # /api/v2/search/*
│       │   │   └── sync.py              # /api/v2/sync/*
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── requests.py          # Request models
│       │       └── responses.py         # Response models
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── text_generator.py        # Rich text generation
│       │   └── scoring.py               # Scoring utilities
│       └── scripts/
│           ├── __init__.py
│           └── build_vectors.py         # Initial vector DB build
│
├── data/                                # Vector database storage
│   ├── chroma_students_sql/            # Student embeddings
│   ├── chroma_internships_sql/         # Internship embeddings
│   └── chroma_internship/              # Topic embeddings
│
├── logs/                                # Application logs
│   └── app.log
│
├── .env                                 # Environment variables
├── .env.example                         # Example environment file
├── requirements.txt                     # Python dependencies
└── README.md                            # Project documentation
```

### Key Components

**Main Application** (`app/main.py`):
- Unified FastAPI application
- Combines both systems on port 8000
- Handles routing to V1 and V2 endpoints

**Internship System** (`app/internship/`):
- Topic modeling and clustering
- Automatic internship categorization
- ChromaDB for topic matching

**Recommendation System** (`app/recommendations/`):
- AI-powered student-internship matching
- Hybrid ranking with 15+ signals
- In-memory caching for performance

---

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

### Check if API is Running
```csharp
using var client = new HttpClient();
var response = await client.GetAsync("http://localhost:8000/health");
var content = await response.Content.ReadAsStringAsync();
Console.WriteLine(content);
```

### View All Endpoints
```
http://localhost:8000/docs
```
(Opens Swagger UI - interactive documentation)

---

## 📊 Part 1: Recommendation Engine (`/api/v2`)

### What Does It Do?
Matches students with internships using AI.

---

### 1️⃣ Get Recommended Internships for a Student

**What it does:** Returns internship IDs that match a student's profile

**When to use:** 
- "Recommended for You" page
- Personalized feed
- Email suggestions

**Endpoint:**
```
GET /api/v2/recommendations/internships/{candidate_id}/ids
```

**You send:**
- Student's `candidate_id` (UUID)

**You get back:**
```json
{
  "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
  "total": 15,
  "ids": [
    "internship-id-1",
    "internship-id-2",
    "internship-id-3"
  ]
}
```

**How to use it (.NET):**
```csharp
public async Task<List<Internship>> GetRecommendationsForStudent(Guid candidateId)
{
    using var client = new HttpClient();
    
    // 1. Call the API
    var response = await client.GetAsync(
        $"http://localhost:8000/api/v2/recommendations/internships/{candidateId}/ids"
    );
    
    response.EnsureSuccessStatusCode();
    var json = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<RecommendationResponse>(json);
    
    // 2. You get IDs only
    var internshipIds = data.Ids;
    
    // 3. Fetch full details from YOUR database
    var fullInternships = await _context.Internships
        .Where(i => internshipIds.Contains(i.InternshipId.ToString()))
        .ToListAsync();
    
    // 4. Maintain API ranking order (IMPORTANT!)
    var orderedInternships = internshipIds
        .Select(id => fullInternships.First(i => i.InternshipId.ToString() == id))
        .ToList();
    
    return orderedInternships;
}

// Response Model
public class RecommendationResponse
{
    [JsonPropertyName("candidate_id")]
    public string CandidateId { get; set; }
    
    [JsonPropertyName("total")]
    public int Total { get; set; }
    
    [JsonPropertyName("ids")]
    public List<string> Ids { get; set; }
}
```

**Important:**
- Results are **already sorted** (best match first) - don't change order
- Fast response (~200ms)
- Returns max 50 results

---

### 2️⃣ Get Ranked Candidates for an Internship

**What it does:** Returns student IDs ranked by how well they match an internship

**When to use:**
- Company views applicants
- HR dashboard
- "Best Matches" section

**Endpoint:**
```
GET /api/v2/recommendations/candidates/{internship_id}/ids
```

**You send:**
- Internship's `internship_id` (UUID)

**You get back:**
```json
{
  "internship_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 8,
  "ids": [
    "candidate-id-1",
    "candidate-id-2",
    "candidate-id-3"
  ]
}
```

**How to use it (.NET):**
```csharp
public async Task<List<Candidate>> GetRankedCandidates(Guid internshipId)
{
    using var client = new HttpClient();
    
    // 1. Get ranked candidates
    var response = await client.GetAsync(
        $"http://localhost:8000/api/v2/recommendations/candidates/{internshipId}/ids"
    );
    
    response.EnsureSuccessStatusCode();
    var json = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<CandidateRecommendationResponse>(json);
    
    // 2. Fetch full profiles from YOUR database
    var candidateIds = data.Ids;
    var profiles = await _context.Candidates
        .Where(c => candidateIds.Contains(c.CandidateId.ToString()))
        .ToListAsync();
    
    // 3. Maintain ranking order
    var orderedProfiles = candidateIds
        .Select(id => profiles.First(c => c.CandidateId.ToString() == id))
        .ToList();
    
    return orderedProfiles;
}

public class CandidateRecommendationResponse
{
    [JsonPropertyName("internship_id")]
    public string InternshipId { get; set; }
    
    [JsonPropertyName("total")]
    public int Total { get; set; }
    
    [JsonPropertyName("ids")]
    public List<string> Ids { get; set; }
}
```

**Important:**
- Only shows candidates **who already applied**
- Already ranked (best match first)
- Fast response (~150ms)

---

### 3️⃣ Search Internships (Semantic Search)

**What it does:** Search internships using natural language (not just keywords)

**When to use:**
- Search bar
- "Find internships about X"
- Smart filters

**Endpoint:**
```
POST /api/v2/search/internships/ids
```

**You send:**
```json
{
  "query": "machine learning internship with python",
  "top_k": 20
}
```

**You get back:**
```json
{
  "candidate_id": "machine learning internship with python",
  "total": 20,
  "ids": [
    "internship-id-1",
    "internship-id-2"
  ]
}
```

**How to use it (.NET):**
```csharp
public async Task<List<Internship>> SearchInternships(string searchQuery, int topK = 20)
{
    using var client = new HttpClient();
    
    // 1. Prepare request
    var requestBody = new
    {
        query = searchQuery,
        top_k = topK
    };
    
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    // 2. Call API
    var response = await client.PostAsync(
        "http://localhost:8000/api/v2/search/internships/ids",
        content
    );
    
    response.EnsureSuccessStatusCode();
    var responseJson = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<RecommendationResponse>(responseJson);
    
    // 3. Fetch from database
    var internshipIds = data.Ids;
    var results = await _context.Internships
        .Where(i => internshipIds.Contains(i.InternshipId.ToString()))
        .ToListAsync();
    
    // 4. Maintain order
    var orderedResults = internshipIds
        .Select(id => results.First(i => i.InternshipId.ToString() == id))
        .ToList();
    
    return orderedResults;
}
```

**Cool Feature:**
- Understands meaning, not just keywords
- "ML Engineer" matches "Machine Learning" ✅
- "Backend Developer" matches "Server-Side Engineer" ✅

---

### 4️⃣ Sync New Student (Add to Recommendations)

**What it does:** Tells the system about a new/updated student so they get recommendations

**When to use:**
- New student registers
- Student updates their profile
- Student adds new skills/projects

**Endpoint:**
```
POST /api/v2/sync/candidate
```

**You send:**
```json
{
  "candidate_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**You get back:**
```json
{
  "success": true,
  "candidate_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Candidate sync task queued successfully. Processing in background.",
  "timestamp": "2024-01-15T10:30:00"
}
```

**How to use it (.NET):**
```csharp
public async Task SyncCandidateToRecommendationEngine(Guid candidateId)
{
    using var client = new HttpClient();
    
    // Prepare request
    var requestBody = new { candidate_id = candidateId.ToString() };
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    // Call API
    var response = await client.PostAsync(
        "http://localhost:8000/api/v2/sync/candidate",
        content
    );
    
    response.EnsureSuccessStatusCode();
}

// Use it after student profile update
public async Task OnStudentProfileUpdate(Candidate candidate)
{
    // 1. Update YOUR database first
    _context.Candidates.Update(candidate);
    await _context.SaveChangesAsync();
    
    // 2. Tell the recommendation system
    await SyncCandidateToRecommendationEngine(candidate.CandidateId);
    
    // 3. Done! System updates in background
}
```

**Important:**
- Runs in **background** (doesn't block)
- Updates usually complete in ~1 second
- Student gets updated recommendations immediately after

---

### 5️⃣ Sync New Internship (Add to System)

**What it does:** Tells the system about a new internship

**When to use:**
- Company posts new internship
- Internship details updated

**Endpoint:**
```
POST /api/v2/sync/internship
```

**You send:**
```json
{
  "internship_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**You get back:**
```json
{
  "success": true,
  "internship_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Internship sync task queued successfully. Processing in background.",
  "timestamp": "2024-01-15T10:30:00"
}
```

**How to use it (.NET):**
```csharp
public async Task SyncInternshipToRecommendationEngine(Guid internshipId)
{
    using var client = new HttpClient();
    
    var requestBody = new { internship_id = internshipId.ToString() };
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await client.PostAsync(
        "http://localhost:8000/api/v2/sync/internship",
        content
    );
    
    response.EnsureSuccessStatusCode();
}

// Use it after new internship is posted
public async Task OnNewInternshipPosted(Internship internship)
{
    // 1. Save to YOUR database first
    await _context.Internships.AddAsync(internship);
    await _context.SaveChangesAsync();
    
    // 2. Tell the recommendation system
    await SyncInternshipToRecommendationEngine(internship.InternshipId);
    
    // 3. Done! Now students can get recommended this internship
}
```

---

### 6️⃣ Delete Candidate (Remove from System)

**What it does:** Removes a student from recommendations

**When to use:**
- Student deletes account
- Student deactivates profile

**Endpoint:**
```
DELETE /api/v2/sync/candidate/{candidate_id}
```

**How to use it (.NET):**
```csharp
public async Task DeleteCandidateFromRecommendations(Guid candidateId)
{
    using var client = new HttpClient();
    
    var response = await client.DeleteAsync(
        $"http://localhost:8000/api/v2/sync/candidate/{candidateId}"
    );
    
    response.EnsureSuccessStatusCode();
}
```

---

### 7️⃣ Delete Internship (Remove from System)

**What it does:** Removes an internship from recommendations

**When to use:**
- Internship closed/deleted
- Position filled

**Endpoint:**
```
DELETE /api/v2/sync/internship/{internship_id}
```

**How to use it (.NET):**
```csharp
public async Task DeleteInternshipFromRecommendations(Guid internshipId)
{
    using var client = new HttpClient();
    
    var response = await client.DeleteAsync(
        $"http://localhost:8000/api/v2/sync/internship/{internshipId}"
    );
    
    response.EnsureSuccessStatusCode();
}
```

---

## 🎯 Part 2: Topic Modeling System (`/api/v1`)

### What Does It Do?
Automatically organizes internships into topics (categories).

**Example Topics:**
- Backend Development (87 internships)
- Frontend Development (65 internships)
- Data Science (43 internships)
- UX/UI Design (38 internships)

---

### 1️⃣ Trigger Full Re-Clustering

**What it does:** Re-analyzes ALL internships and creates new topics

**When to use:**
- Weekly/monthly maintenance
- Major database changes
- Admin wants to refresh categories

**Endpoint:**
```
POST /api/v1/topics/cluster-all-async
```

**You send:**
```json
{
  "topic_version": "v2.0",
  "n_topics": "auto"
}
```

**You get back (immediately):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Clustering started in background",
  "check_status_url": "/api/v1/topics/job/abc-123-def-456"
}
```

**How to use it (.NET):**
```csharp
public async Task<string> StartClustering(string topicVersion = "auto", string nTopics = "auto")
{
    using var client = new HttpClient();
    
    // 1. Start clustering
    var requestBody = new
    {
        topic_version = topicVersion,
        n_topics = nTopics
    };
    
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await client.PostAsync(
        "http://localhost:8000/api/v1/topics/cluster-all-async",
        content
    );
    
    response.EnsureSuccessStatusCode();
    var responseJson = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<ClusteringJobResponse>(responseJson);
    
    return data.JobId;
}

// Monitor progress
public async Task<ClusteringStatus> CheckClusteringStatus(string jobId)
{
    using var client = new HttpClient();
    
    var response = await client.GetAsync(
        $"http://localhost:8000/api/v1/topics/job/{jobId}"
    );
    
    response.EnsureSuccessStatusCode();
    var json = await response.Content.ReadAsStringAsync();
    var status = JsonSerializer.Deserialize<ClusteringStatus>(json);
    
    return status;
}

// Poll until complete
public async Task<ClusteringStatus> WaitForClusteringComplete(string jobId)
{
    ClusteringStatus status;
    
    do
    {
        await Task.Delay(5000); // Wait 5 seconds
        status = await CheckClusteringStatus(jobId);
        
        if (status.Status == "failed")
        {
            throw new Exception($"Clustering failed: {status.Error}");
        }
    }
    while (status.Status != "completed");
    
    return status;
}

// Response Models
public class ClusteringJobResponse
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("message")]
    public string Message { get; set; }
}

public class ClusteringStatus
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("topic_version")]
    public string TopicVersion { get; set; }
    
    [JsonPropertyName("error")]
    public string Error { get; set; }
    
    [JsonPropertyName("result")]
    public ClusteringResult Result { get; set; }
}

public class ClusteringResult
{
    [JsonPropertyName("n_topics")]
    public int NTopics { get; set; }
    
    [JsonPropertyName("total_internships")]
    public int TotalInternships { get; set; }
    
    [JsonPropertyName("silhouette_score")]
    public double SilhouetteScore { get; set; }
}
```

**Important:**
- Takes **2-3 minutes** to complete
- Runs in background
- System remains usable during clustering
- Poll the status endpoint to track progress

---

### 2️⃣ Assign Topic to Single Internship

**What it does:** Finds the best topic for one internship

**When to use:**
- New internship posted
- Internship details updated

**Endpoint:**
```
POST /api/v1/assignments/assign-async
```

**You send:**
```json
{
  "internship_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**You get back (immediately):**
```json
{
  "job_id": "xyz-789",
  "status": "pending",
  "internship_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Assignment started in background",
  "check_status_url": "/api/v1/assignments/single-job/xyz-789"
}
```

**How to use it (.NET):**
```csharp
public async Task<Guid?> AssignTopicToInternship(Guid internshipId)
{
    using var client = new HttpClient();
    
    // 1. Request topic assignment
    var requestBody = new { internship_id = internshipId.ToString() };
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await client.PostAsync(
        "http://localhost:8000/api/v1/assignments/assign-async",
        content
    );
    
    response.EnsureSuccessStatusCode();
    var responseJson = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<AssignmentJobResponse>(responseJson);
    
    // 2. Wait for completion (usually < 1 second)
    await Task.Delay(1000);
    
    // 3. Check status
    var statusResponse = await client.GetAsync(
        $"http://localhost:8000/api/v1/assignments/single-job/{data.JobId}"
    );
    
    statusResponse.EnsureSuccessStatusCode();
    var statusJson = await statusResponse.Content.ReadAsStringAsync();
    var status = JsonSerializer.Deserialize<AssignmentStatus>(statusJson);
    
    if (status.Status == "completed" && status.Result != null)
    {
        // 4. Update YOUR database with topic_id
        var topicId = Guid.Parse(status.Result.TopicId);
        
        var internship = await _context.Internships
            .FirstAsync(i => i.InternshipId == internshipId);
        
        internship.CurrentTopicId = topicId;
        await _context.SaveChangesAsync();
        
        return topicId;
    }
    
    return null;
}

// Use in new internship workflow
public async Task OnNewInternshipPosted(Internship internship)
{
    // 1. Save to database
    await _context.Internships.AddAsync(internship);
    await _context.SaveChangesAsync();
    
    // 2. Sync to recommendation system
    await SyncInternshipToRecommendationEngine(internship.InternshipId);
    
    // 3. Assign topic
    var topicId = await AssignTopicToInternship(internship.InternshipId);
    
    if (topicId.HasValue)
    {
        Console.WriteLine($"Internship assigned to topic: {topicId}");
    }
}

// Response Models
public class AssignmentJobResponse
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("internship_id")]
    public string InternshipId { get; set; }
}

public class AssignmentStatus
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("result")]
    public AssignmentResult Result { get; set; }
}

public class AssignmentResult
{
    [JsonPropertyName("internship_id")]
    public string InternshipId { get; set; }
    
    [JsonPropertyName("topic_id")]
    public string TopicId { get; set; }
    
    [JsonPropertyName("topic_number")]
    public int TopicNumber { get; set; }
    
    [JsonPropertyName("label")]
    public string Label { get; set; }
    
    [JsonPropertyName("confidence")]
    public double? Confidence { get; set; }
}
```

**Important:**
- Usually completes in **< 1 second**
- Updates database automatically
- Returns topic name and confidence score

---

### 3️⃣ Batch Assign Topics

**What it does:** Assign topics to multiple internships at once

**When to use:**
- Bulk import of internships
- Weekly batch processing

**Endpoint:**
```
POST /api/v1/assignments/assign-batch-async
```

**You send:**
```json
{
  "internship_ids": [
    "id-1",
    "id-2",
    "id-3",
    "id-4"
  ]
}
```

**You get back (immediately):**
```json
{
  "job_id": "batch-456",
  "status": "pending",
  "total": 4,
  "message": "Batch assignment started in background",
  "check_status_url": "/api/v1/assignments/job/batch-456"
}
```

**How to use it (.NET):**
```csharp
public async Task<string> AssignTopicsToBatch(List<Guid> internshipIds)
{
    using var client = new HttpClient();
    
    // 1. Start batch assignment
    var requestBody = new
    {
        internship_ids = internshipIds.Select(id => id.ToString()).ToList()
    };
    
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await client.PostAsync(
        "http://localhost:8000/api/v1/assignments/assign-batch-async",
        content
    );
    
    response.EnsureSuccessStatusCode();
    var responseJson = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<BatchAssignmentJobResponse>(responseJson);
    
    return data.JobId;
}

// Monitor batch progress
public async Task<BatchAssignmentStatus> WaitForBatchComplete(string jobId)
{
    using var client = new HttpClient();
    BatchAssignmentStatus status;
    
    do
    {
        await Task.Delay(2000); // Check every 2 seconds
        
        var response = await client.GetAsync(
            $"http://localhost:8000/api/v1/assignments/job/{jobId}"
        );
        
        response.EnsureSuccessStatusCode();
        var json = await response.Content.ReadAsStringAsync();
        status = JsonSerializer.Deserialize<BatchAssignmentStatus>(json);
        
        if (status.Status == "failed")
        {
            throw new Exception($"Batch assignment failed: {status.Error}");
        }
    }
    while (status.Status != "completed");
    
    return status;
}

public class BatchAssignmentJobResponse
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("total")]
    public int Total { get; set; }
}

public class BatchAssignmentStatus
{
    [JsonPropertyName("job_id")]
    public string JobId { get; set; }
    
    [JsonPropertyName("status")]
    public string Status { get; set; }
    
    [JsonPropertyName("error")]
    public string Error { get; set; }
    
    [JsonPropertyName("result")]
    public BatchAssignmentResult Result { get; set; }
}

public class BatchAssignmentResult
{
    [JsonPropertyName("total")]
    public int Total { get; set; }
    
    [JsonPropertyName("assigned")]
    public int Assigned { get; set; }
    
    [JsonPropertyName("failed")]
    public int Failed { get; set; }
}
```

---

### 4️⃣ Deactivate a Topic

**What it does:** Mark a topic as inactive (won't be used for new assignments)

**When to use:**
- Topic no longer relevant
- Merging topics
- Cleaning up old categories

**Endpoint:**
```
PUT /api/v1/topics/{topic_id}/deactivate
```

**How to use it (.NET):**
```csharp
public async Task DeactivateTopic(Guid topicId)
{
    using var client = new HttpClient();
    
    var response = await client.PutAsync(
        $"http://localhost:8000/api/v1/topics/{topicId}/deactivate",
        null
    );
    
    response.EnsureSuccessStatusCode();
}
```

---

## 📋 Common Integration Workflows

### Workflow 1: New Student Registers

```csharp
public async Task OnStudentRegistration(Candidate candidate)
{
    // 1. Save to YOUR database first
    await _context.Candidates.AddAsync(candidate);
    await _context.SaveChangesAsync();
    
    // 2. Tell recommendation system
    using var client = new HttpClient();
    var requestBody = new { candidate_id = candidate.CandidateId.ToString() };
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    await client.PostAsync(
        "http://localhost:8000/api/v2/sync/candidate",
        content
    );
    
    // 3. Done! Student can now get recommendations
}
```

---

### Workflow 2: Company Posts New Internship

```csharp
public async Task OnNewInternshipPost(Internship internship)
{
    using var client = new HttpClient();
    
    // 1. Save to YOUR database
    await _context.Internships.AddAsync(internship);
    await _context.SaveChangesAsync();
    
    // 2. Tell recommendation system
    var syncBody = new { internship_id = internship.InternshipId.ToString() };
    var syncJson = JsonSerializer.Serialize(syncBody);
    var syncContent = new StringContent(syncJson, Encoding.UTF8, "application/json");
    
    await client.PostAsync(
        "http://localhost:8000/api/v2/sync/internship",
        syncContent
    );
    
    // 3. Assign topic
    var assignBody = new { internship_id = internship.InternshipId.ToString() };
    var assignJson = JsonSerializer.Serialize(assignBody);
    var assignContent = new StringContent(assignJson, Encoding.UTF8, "application/json");
    
    var assignResponse = await client.PostAsync(
        "http://localhost:8000/api/v1/assignments/assign-async",
        assignContent
    );
    
    var assignResponseJson = await assignResponse.Content.ReadAsStringAsync();
    var assignData = JsonSerializer.Deserialize<AssignmentJobResponse>(assignResponseJson);
    
    // 4. Wait for topic assignment (usually < 1 second)
    await Task.Delay(1000);
    
    // 5. Get result
    var statusResponse = await client.GetAsync(
        $"http://localhost:8000/api/v1/assignments/single-job/{assignData.JobId}"
    );
    
    if (statusResponse.IsSuccessStatusCode)
    {
        var statusJson = await statusResponse.Content.ReadAsStringAsync();
        var status = JsonSerializer.Deserialize<AssignmentStatus>(statusJson);
        
        if (status.Status == "completed" && status.Result != null)
        {
            // Update database with topic
            internship.CurrentTopicId = Guid.Parse(status.Result.TopicId);
            await _context.SaveChangesAsync();
        }
    }
}
```

---

### Workflow 3: Show Recommendations to Student

```csharp
public async Task<List<Internship>> GetRecommendationsPage(Guid candidateId)
{
    using var client = new HttpClient();
    
    // 1. Get recommended IDs
    var response = await client.GetAsync(
        $"http://localhost:8000/api/v2/recommendations/internships/{candidateId}/ids"
    );
    
    response.EnsureSuccessStatusCode();
    var json = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<RecommendationResponse>(json);
    
    // 2. Fetch full details from YOUR database
    var internshipIds = data.Ids.Select(Guid.Parse).ToList();
    var internships = await _context.Internships
        .Where(i => internshipIds.Contains(i.InternshipId) && !i.IsDeleted)
        .ToListAsync();
    
    // 3. Maintain API ranking order (IMPORTANT!)
    var orderedInternships = data.Ids
        .Select(id => internships.First(i => i.InternshipId.ToString() == id))
        .ToList();
    
    return orderedInternships;
}
```

---

### Workflow 4: Weekly Topic Refresh

```csharp
public async Task WeeklyTopicUpdate()
{
    using var client = new HttpClient();
    
    // 1. Trigger re-clustering
    var requestBody = new
    {
        topic_version = $"v_{DateTime.Now:yyyyMMdd}",
        n_topics = "auto"
    };
    
    var json = JsonSerializer.Serialize(requestBody);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    var response = await client.PostAsync(
        "http://localhost:8000/api/v1/topics/cluster-all-async",
        content
    );
    
    response.EnsureSuccessStatusCode();
    var responseJson = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<ClusteringJobResponse>(responseJson);
    
    var jobId = data.JobId;
    
    // 2. Monitor progress
    ClusteringStatus status;
    do
    {
        await Task.Delay(10000); // Check every 10 seconds
        
        var statusResponse = await client.GetAsync(
            $"http://localhost:8000/api/v1/topics/job/{jobId}"
        );
        
        var statusJson = await statusResponse.Content.ReadAsStringAsync();
        status = JsonSerializer.Deserialize<ClusteringStatus>(statusJson);
        
        if (status.Status == "completed")
        {
            Console.WriteLine("✅ Topics updated!");
            Console.WriteLine($"Created {status.Result.NTopics} topics");
            Console.WriteLine($"Processed {status.Result.TotalInternships} internships");
            
            // 3. Notify admins
            await SendAdminNotification(new
            {
                Message = "Weekly topic update completed",
                Topics = status.Result.NTopics,
                Quality = status.Result.SilhouetteScore
            });
        }
        else if (status.Status == "failed")
        {
            Console.WriteLine($"❌ Failed: {status.Error}");
            await SendAdminAlert(status.Error);
        }
    }
    while (status.Status != "completed" && status.Status != "failed");
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | What to Do |
|------|---------|-----------|
| 200 | Success | Process response |
| 202 | Accepted (Async) | Poll job status |
| 404 | Not Found | Check ID exists in database |
| 500 | Server Error | Log error, retry later |

### Common Errors

**1. "Candidate not found"**
```json
{
  "detail": "Candidate 123e4567... not found"
}
```
**Cause:** Student doesn't exist in the system  
**Fix:** Call `/api/v2/sync/candidate` first

---

**2. "Job not found"**
```json
{
  "detail": "Job not found"
}
```
**Cause:** Invalid job_id or job expired  
**Fix:** Check job_id is correct

---

**3. "No matching topic available"**
```json
{
  "status": "failed",
  "error": "Internship not found, has insufficient text, or no matching topic available"
}
```
**Cause:** Internship description too short or no topics exist  
**Fix:** Ensure internship has proper title/description, run clustering first

---

## ✅ Best Practices

### 1. **Always Update Your Database First**
```csharp
// ✅ Correct order
await _context.Candidates.AddAsync(student);
await _context.SaveChangesAsync();         // 1. Your database
await SyncToRecommendationAPI(studentId);  // 2. Then API

// ❌ Wrong order
await SyncToRecommendationAPI(studentId);  // API looks for data...
await _context.Candidates.AddAsync(student);
await _context.SaveChangesAsync();         // ...but it's not there yet!
```

### 2. **Don't Change Recommendation Order**
```csharp
// ✅ Correct - Keep API ranking
var ids = data.Ids;
var internships = await _context.Internships
    .Where(i => ids.Contains(i.InternshipId.ToString()))
    .ToListAsync();
    
// Maintain order from API
var ordered = ids.Select(id => 
    internships.First(i => i.InternshipId.ToString() == id)
).ToList();

// ❌ Wrong - Destroys AI ranking
var ordered = internships.OrderBy(i => i.Salary).ToList(); // Don't do this!
```

### 3. **Handle Async Operations Properly**
```csharp
// ✅ Good - Poll for status
var jobId = await StartClustering();
var result = await WaitForComplete(jobId);

// ❌ Bad - Expecting instant result
var jobId = await StartClustering();
var result = await GetJobStatus(jobId); // Still pending!
```

### 4. **Sync Changes to Recommendation System**
```csharp
// When student updates profile
await _context.SaveChangesAsync();
await SyncCandidateToAPI(candidateId);

// When internship is updated
await _context.SaveChangesAsync();
await SyncInternshipToAPI(internshipId);

// When internship is deleted
internship.IsDeleted = true;
await _context.SaveChangesAsync();
await DeleteInternshipFromAPI(internshipId);
```

### 5. **Use Batch Operations When Possible**
```csharp
// ✅ Good - Batch assign 100 internships
var jobId = await AssignTopicsToBatch(internshipIds);

// ❌ Bad - 100 separate requests
foreach (var id in internshipIds)
{
    await AssignTopicToInternship(id);
}
```

### 6. **Use HttpClientFactory in Production**
```csharp
// Register in Startup.cs
services.AddHttpClient("RecommendationAPI", client =>
{
    client.BaseAddress = new Uri("http://localhost:8000");
    client.Timeout = TimeSpan.FromSeconds(30);
});

// Use in service
public class RecommendationService
{
    private readonly IHttpClientFactory _clientFactory;
    
    public RecommendationService(IHttpClientFactory clientFactory)
    {
        _clientFactory = clientFactory;
    }
    
    public async Task<List<Internship>> GetRecommendations(Guid candidateId)
    {
        var client = _clientFactory.CreateClient("RecommendationAPI");
        // Use client...
    }
}
```

---

## 🔧 Troubleshooting

### Issue: Recommendations not showing for new student

**Check:**
1. Did you call `/api/v2/sync/candidate` after registration?
2. Does student have complete profile (skills, interests, etc.)?
3. Check API health:
```csharp
var response = await client.GetAsync("http://localhost:8000/health");
var content = await response.Content.ReadAsStringAsync();
Console.WriteLine(content);
```

---

### Issue: Internship not getting topic assigned

**Check:**
1. Did you call `/api/v1/assignments/assign-async`?
2. Does internship have title and description?
3. Have you run clustering at least once?

---

### Issue: Slow responses

**Check:**
1. Are you calling the API in a loop? (Use batch operations)
2. Is your network connection stable?
3. Check server logs for errors

---

## 📞 Quick Reference

### Recommendation Engine
| Task | Endpoint | Method |
|------|----------|--------|
| Get recommendations for student | `/api/v2/recommendations/internships/{id}/ids` | GET |
| Get candidates for internship | `/api/v2/recommendations/candidates/{id}/ids` | GET |
| Search internships | `/api/v2/search/internships/ids` | POST |
| Sync new student | `/api/v2/sync/candidate` | POST |
| Sync new internship | `/api/v2/sync/internship` | POST |
| Delete student | `/api/v2/sync/candidate/{id}` | DELETE |
| Delete internship | `/api/v2/sync/internship/{id}` | DELETE |

### Topic Modeling
| Task | Endpoint | Method |
|------|----------|--------|
| Re-cluster all internships | `/api/v1/topics/cluster-all-async` | POST |
| Check clustering status | `/api/v1/topics/job/{job_id}` | GET |
| Assign single internship | `/api/v1/assignments/assign-async` | POST |
| Check assignment status | `/api/v1/assignments/single-job/{job_id}` | GET |
| Batch assign internships | `/api/v1/assignments/assign-batch-async` | POST |
| Check batch status | `/api/v1/assignments/job/{job_id}` | GET |
| Deactivate topic | `/api/v1/topics/{id}/deactivate` | PUT |

---

## 🎯 Summary

**Two systems, one API:**
- **V2 (Recommendations)** - Match students with internships
- **V1 (Topics)** - Auto-categorize internships

**Key Points for .NET Developers:**
- ✅ Use `HttpClient` or `HttpClientFactory`
- ✅ All endpoints return JSON (use `JsonSerializer`)
- ✅ Long operations are async (poll for status)
- ✅ Always sync changes to the API
- ✅ Keep recommendation order
- ✅ Update your database first, then sync
- ✅ Use proper async/await patterns

**Need Help?**
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

**Happy Integrating! 🚀**
