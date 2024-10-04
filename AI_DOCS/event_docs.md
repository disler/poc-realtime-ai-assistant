# Realtime API Events

# Realtime API Events

- Session Configuration
  • session.update
    - Configures the connection-wide behavior of the conversation session
    - Typically sent immediately after connecting
    - Can be sent at any point to reconfigure behavior after the current response is complete

- Input Audio
  • input_audio_buffer.append
    - Appends audio data to the shared user input buffer
    - Audio not processed until end of speech detected or manual response.create sent
  • input_audio_buffer.clear
    - Clears the current audio input buffer
    - Does not impact responses already in progress
  • input_audio_buffer.commit
    - Commits current state of user input buffer to subscribed conversations
    - Includes it as information for the next response

- Item Management (for establishing history or including non-audio item information)
  • conversation.item.create
    - Inserts a new item into the conversation
    - Can be positioned according to previous_item_id
    - Provides new input, tool responses, or historical information
  • conversation.item.delete
    - Removes an item from an existing conversation
  • conversation.item.truncate
    - Manually shortens text and/or audio content in a message
    - Useful for situations with faster-than-realtime model generation

- Response Management
  • response.create
    - Initiates model processing of unprocessed conversation input
    - Signifies the end of the caller's logical turn
    - Must be called for text input, tool responses, none mode, etc.
  • response.cancel
    - Cancels an in-progress response

- Responses: commands sent by the /realtime endpoint to the caller
  • session.created
    - Sent upon successful connection establishment
    - Provides a connection-specific ID for debugging or logging
  • session.updated
    - Sent in response to a session.update event
    - Reflects changes made to the session configuration

- Caller Item Acknowledgement
  • conversation.item.created
    - Acknowledges insertion of a new conversation item
  • conversation.item.deleted
    - Acknowledges removal of an existing conversation item
  • conversation.item.truncated
    - Acknowledges truncation of an existing conversation item

- Response Flow
  • response.created
    - Notifies start of a new response for a conversation
    - Snapshots input state and begins generation of new items
  • response.done
    - Notifies completion of response generation
  • rate_limits.updated
    - Sent after response.done
    - Provides current rate limit information

- Item Flow in a Response
  • response.output_item.added
    - Notifies creation of a new, server-generated conversation item
  • response_output_item_done
    - Notifies completion of a new conversation item's addition

- Content Flow within Response Items
  • response.content_part.added
    - Notifies creation of a new content part within a conversation item
  • response.content_part.done
    - Signals completion of a newly created content part
  • response.audio.delta
    - Provides incremental update to binary audio data
  • response.audio.done
    - Signals completion of audio content part updates
  • response.audio_transcript.delta
    - Provides incremental update to audio transcription
  • response.audio_transcript.done
    - Signals completion of audio transcription updates
  • response.text.delta
    - Provides incremental update to text content
  • response.text.done
    - Signals completion of text content updates
  • response.function_call_arguments.delta
    - Provides incremental update to function call arguments
  • response.function_call_arguments.done
    - Signals completion of function call arguments

- User Input Audio
  • input_audio_buffer.speech_started
    - Notifies detection of speech start in input audio buffer
  • input_audio_buffer.speech_stopped
    - Notifies detection of speech end in input audio buffer
  • conversation.item.input_audio_transcription.completed
    - Notifies availability of input audio transcription
  • conversation.item_input_audio_transcription.failed
    - Notifies failure of input audio transcription
  • input_audio_buffer_committed
    - Acknowledges submission of user audio input buffer
  • input_audio_buffer_cleared
    - Acknowledges clearing of pending user audio input buffer

- Other
  • error
    - Indicates processing error in the session
    - Includes detailed error message