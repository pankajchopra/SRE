import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.RetryRegistry;
import io.github.resilience4j.retry.annotation.Retry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.Marker;
import org.slf4j.MarkerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class ExternalCallService {

    private static final Logger LOGGER = LoggerFactory.getLogger(ExternalCallService.class);
    private static final MarkerFactory MARKER_FACTORY = new MarkerFactory();

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private RetryRegistry retryRegistry;

    @CircuitBreaker(name = "externalCallsCircuitBreaker", fallbackMethod = "getDataFallback")
    @Retry(name = "externalCallsRetry")
    public ResponseEntity<?> makeACall(String targetUriStr, HttpMethod targetMethod, HttpEntity<String> entity, boolean stringReturnType)
            throws RestClientException {

        Map<String, Object> headers = getFromEntity(entity);
        Marker headersMarker = MARKER_FACTORY.getMarker(String.valueOf(headers));
        LOGGER.debug(headersMarker, "Before Call ({})", targetUriStr);

        if (stringReturnType) {
            ResponseEntity<String> response = this.restTemplate.exchange(targetUriStr, targetMethod, entity, String.class);
            headers.putAll(getRetryMetrics(retryRegistry, "externalCallsRetry"));
            LOGGER.debug(MARKER_FACTORY.getMarker(String.valueOf(headers)), "After Call ({})", targetUriStr);
            return response;
        } else {
            ResponseEntity<Object> response = this.restTemplate.exchange(targetUriStr, targetMethod, entity, Object.class);
            headers.putAll(getRetryMetrics(retryRegistry, "externalCallsRetry"));
            LOGGER.debug(MARKER_FACTORY.getMarker(String.valueOf(headers)), "After Call ({})", targetUriStr);
            return response;
        }
    }

    /**
     * Fallback method for the circuit breaker. Must have the same signature as the original method,
     * plus a Throwable parameter at the end.
     */
    public ResponseEntity<?> getDataFallback(String targetUriStr, HttpMethod targetMethod, HttpEntity<String> entity, boolean stringReturnType, Throwable t) {
        LOGGER.error("Fallback initiated for call to {} due to: {}", targetUriStr, t.getMessage());
        Map<String, String> fallbackBody = Map.of(
            "error", "Service is currently unavailable.",
            "message", "Please try again later."
        );
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(fallbackBody);
    }

    // Helper method to extract headers from the entity
    private Map<String, Object> getFromEntity(HttpEntity<String> entity) {
        if (entity != null && entity.getHeaders() != null) {
            return entity.getHeaders().toSingleValueMap().entrySet().stream()
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue, (a, b) -> b, HashMap::new));
        }
        return new HashMap<>();
    }

    // Helper method to simulate getting retry metrics
    private Map<String, String> getRetryMetrics(RetryRegistry registry, String retryName) {
        // In a real application, you might get actual metrics from the registry.
        // For this example, we return a dummy map.
        return Map.of("retry-metrics", "checked");
    }
}




import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import io.github.resilience4j.retry.RetryRegistry;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ExternalCallServiceTest {

    @Mock
    private RestTemplate restTemplate;

    @Mock
    private RetryRegistry retryRegistry; // Mocked but not used in these unit tests

    @InjectMocks
    private ExternalCallService externalCallService;

    private HttpEntity<String> httpEntity;
    private String targetUri;
    private HttpMethod targetMethod;

    @BeforeEach
    void setUp() {
        targetUri = "http://example.com/api/v1/data";
        targetMethod = HttpMethod.POST;
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        httpEntity = new HttpEntity<>("{\"key\":\"value\"}", headers);
    }

    @Test
    void makeACall_ShouldReturnStringResponse_WhenStringReturnTypeIsTrue() {
        // Arrange
        String responseBody = "{\"status\":\"success\"}";
        ResponseEntity<String> expectedResponse = new ResponseEntity<>(responseBody, HttpStatus.OK);
        when(restTemplate.exchange(targetUri, targetMethod, httpEntity, String.class)).thenReturn(expectedResponse);

        // Act
        ResponseEntity<?> actualResponse = externalCallService.makeACall(targetUri, targetMethod, httpEntity, true);

        // Assert
        assertNotNull(actualResponse);
        assertEquals(HttpStatus.OK, actualResponse.getStatusCode());
        assertEquals(responseBody, actualResponse.getBody());
        verify(restTemplate, times(1)).exchange(targetUri, targetMethod, httpEntity, String.class);
        verify(restTemplate, never()).exchange(anyString(), any(), any(), eq(Object.class));
    }

    @Test
    void makeACall_ShouldReturnObjectResponse_WhenStringReturnTypeIsFalse() {
        // Arrange
        Map<String, String> responseBody = Map.of("status", "success");
        ResponseEntity<Object> expectedResponse = new ResponseEntity<>(responseBody, HttpStatus.OK);
        when(restTemplate.exchange(targetUri, targetMethod, httpEntity, Object.class)).thenReturn(expectedResponse);

        // Act
        ResponseEntity<?> actualResponse = externalCallService.makeACall(targetUri, targetMethod, httpEntity, false);

        // Assert
        assertNotNull(actualResponse);
        assertEquals(HttpStatus.OK, actualResponse.getStatusCode());
        assertEquals(responseBody, actualResponse.getBody());
        verify(restTemplate, times(1)).exchange(targetUri, targetMethod, httpEntity, Object.class);
        verify(restTemplate, never()).exchange(anyString(), any(), any(), eq(String.class));
    }

    @Test
    void makeACall_ShouldThrowException_WhenRestTemplateThrowsException() {
        // Arrange
        when(restTemplate.exchange(targetUri, targetMethod, httpEntity, String.class))
            .thenThrow(new RestClientException("Connection failed"));

        // Act & Assert
        assertThrows(RestClientException.class, () -> {
            externalCallService.makeACall(targetUri, targetMethod, httpEntity, true);
        });

        // Verify that the method was still called once
        verify(restTemplate, times(1)).exchange(targetUri, targetMethod, httpEntity, String.class);
    }
}
