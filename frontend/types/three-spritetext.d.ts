declare module 'three-spritetext' {
  import { Object3D, Vector3 } from 'three';
  
  export default class SpriteText extends Object3D {
    constructor(text?: string, textHeight?: number, color?: string);
    
    text: string;
    textHeight: number;
    color: string;
    fontFace: string;
    fontSize: number;
    fontWeight: string;
    padding: number;
    backgroundColor: string | false;
    borderColor: string | false;
    borderWidth: number;
    borderRadius: number;
    strokeColor: string | false;
    strokeWidth: number;
    
    position: Vector3;
    
    clone(): SpriteText;
    copy(source: SpriteText): this;
    dispose(): void;
  }
}