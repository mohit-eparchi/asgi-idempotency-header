import asyncio
from collections.abc import Awaitable, Callable
from uuid import uuid4

import pytest
from httpx import Response

from tests.conftest import dummy_response

pytestmark = pytest.mark.asyncio

http_call = Callable[..., Awaitable[Response]]


async def test_no_idempotence(applicable_method: http_call) -> None:
    response = await applicable_method("/json-response")
    assert response.json() == dummy_response
    assert dict(response.headers) == {
        "content-length": "15",
        "content-type": "application/json",
    }


json_response_endpoints = [
    "/json-response",
    "/dict-response",
    "/normal-response",
    "/normal-byte-response",
    "/orjson-response",
    "/ujson-response",
]


@pytest.mark.parametrize("endpoint", json_response_endpoints)
async def test_idempotence_works_for_json_responses(
    applicable_method: http_call, endpoint: str
) -> None:
    idempotency_header = {"Idempotency-Key": uuid4().hex}

    # First request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert response.json() == dummy_response
    assert "idempotent-replayed" not in dict(response.headers)

    # Second request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert response.json() == dummy_response
    assert dict(response.headers)["idempotent-replayed"] == "true"


async def test_expiration_of_idempotency_key_from_active_idempotency_keys(
    applicable_method,
) -> None:
    endpoint = "/json-response"
    idempotency_header = {"Idempotency-Key": uuid4().hex}

    # First request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert response.json() == dummy_response
    assert "idempotent-replayed" not in dict(response.headers)

    # Second request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert response.json() == dummy_response
    assert dict(response.headers)["idempotent-replayed"] == "true"

    # Third request after >2 seconds to test clearing of idempotency key from set
    await asyncio.sleep(2.1)
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert response.json() == dummy_response
    assert "idempotent-replayed" not in dict(response.headers)


other_response_endpoints = [
    "/xml-response",
    "/html-response",
    "/bad-response",
    "/file-response",
    "/plain-text-response",
]


@pytest.mark.parametrize("endpoint", other_response_endpoints)
async def test_non_json_responses(applicable_method: http_call, endpoint: str) -> None:
    idempotency_header = {"Idempotency-Key": uuid4().hex}

    # First request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert "idempotent-replayed" not in dict(response.headers)

    # Second request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert "idempotent-replayed" not in dict(response.headers)


non_json_encoding_endpoints = [
    "/redirect-response",
    "/streaming-response",
]


@pytest.mark.parametrize("endpoint", non_json_encoding_endpoints)
async def test_wrong_response_encoding(
    caplog, applicable_method: http_call, endpoint: str
) -> None:
    idempotency_header = {"Idempotency-Key": uuid4().hex}

    # First request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert "idempotent-replayed" not in dict(response.headers)

    # Second request
    response = await applicable_method(endpoint, headers=idempotency_header)
    assert "idempotent-replayed" not in dict(response.headers)


async def test_idempotent_method(inapplicable_method: http_call) -> None:
    idempotency_header = {"Idempotency-Key": uuid4().hex}
    await inapplicable_method("/idempotent-method", headers=idempotency_header)
    second_response = await inapplicable_method(
        "/idempotent-method", headers=idempotency_header
    )
    assert second_response.headers == {}


async def test_multiple_concurrent_requests(client) -> None:
    id_ = str(uuid4())

    async def fire_request():
        return await client.post("/slow-endpoint", headers={"Idempotency-key": id_})

    count_200 = 0
    responses = await asyncio.gather(
        *[asyncio.create_task(fire_request()) for x in range(20)]
    )
    for response in responses:
        if response.status_code == 200:
            count_200 = count_200 + 1
    assert count_200 == 1


bad_header_values = ["test", uuid4().hex[:-1] + "u", "123", "ssssssssssssssssssss"]


@pytest.mark.parametrize("value", bad_header_values)
async def test_bad_header_formatting(value: str, client) -> None:
    response = await client.post("/json-response", headers={"Idempotency-key": value})
    assert response.json() == {
        "detail": "'Idempotency-Key' header value must be formatted as a v4 UUID"
    }
    assert response.status_code == 422
