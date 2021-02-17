// Uncomment these imports to begin using these cool features!

// import {inject} from '@loopback/core';

//
// export class HelloController {
//   constructor() {}
// }

import {get} from '@loopback/rest';
export class HelloController {
  @get('/hello')
  hello(): string {
    return 'Hello world!';
  }
}
